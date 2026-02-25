import json
import time
from kafka import KafkaConsumer
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert


TOPIC_MAPPING = {
    "station_status": "station_passenger_stats",
    "rail_segments": "runtime_rail_segment_state",
    "platform_status": "runtime_platform_state",
    "world_clock": "runtime_world_clock_state",
    "passenger_travelling_state": "runtime_passenger_state",
    "train_status": "runtime_train_state",
}


TABLE_UNIQUE_KEYS = {
    "runtime_world_clock_state": ["clock_tick"],
    "runtime_rail_segment_state": ["clock_tick", "segment_id"],
    "runtime_passenger_state": ["clock_tick", "passenger_id"],
    "runtime_train_state": ["clock_tick", "train_id"],
    "runtime_platform_state": ["clock_tick", "station_id", "route_id"],
    "station_passenger_stats": ["clock_tick", "station_id"],
}

# NOTE:
# Larger batch sizes will avoid a performance issue with hitting the db so often.
# However, I also want to bend the rules and make the dashboard "realtime"
# so this was my decision to not let the dashboard hang with "stale" data.
# I am aware I am mixing streaming, with downstream dbt marts, and a dashboard, but making it "live".
BATCH_SIZE = 1

DB_CONNECTION = "postgresql://thomas:mind_the_gap@localhost:5432/subway_system"


def get_db_engine():
    return create_engine(DB_CONNECTION)


def consume_and_store():
    topics = list(TOPIC_MAPPING.keys())
    print(f"Connecting to Kafka topics: {topics}...")
    clean_topic_functions = {key: lambda x: x for key in topics}
    #clean_topic_functions["rail_segments"] = clean_rail_segments

    # NOTE: Data recovery strategy
    # In a true production environment, we would use a static 'group.id'
    # (e.g., 'transit_pipeline_prod') so the consumer resumes exactly where
    # it left off after a restart, avoiding unnecessary compute.
    #
    # To execute a historical backfill (Disaster Recovery), we would either:
    #   1. Use the Kafka CLI to reset the group's offsets to 0.
    #   2. Spin up a new consumer with a unique group.id and 'auto.offset.reset': 'earliest'.
    #
    # Because our Postgres landing tables are strictly constrained with UNIQUE
    # composite keys, we can safely replay the entire Kafka retention window.
    # SQLAlchemy's ON CONFLICT DO UPDATE will idempotently heal the state
    # without duplicating historical records.
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=["localhost:9092"],
        group_id="transit_group",
        auto_offset_reset="earliest",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    engine = get_db_engine()
    metadata = MetaData(schema="public_transit")
    buffers = {topic: [] for topic in topics}

    print("Consumer started. Waiting for data...")

    for message in consumer:
        topic = message.topic
        data = message.value
        if topic in buffers:
            buffers[topic].append(data)
            if len(buffers[topic]) >= BATCH_SIZE:
                target_table = TOPIC_MAPPING[topic]
                buffers[topic] = clean_topic_functions[topic](buffers[topic])
                insert_batch(engine, buffers[topic], metadata, target_table)
                buffers[topic] = []


def insert_batch(db_engine, data_list, metadata, table_name):
    if not data_list:
        return

    with db_engine.begin() as conn:
        table = Table(table_name, metadata, autoload_with=db_engine)
        stmt = insert(table).values(data_list)
        unique_cols = TABLE_UNIQUE_KEYS[table_name]

        # Build the dictionary of columns to overwrite if a conflict occurs.
        # 'stmt.excluded' refers to the new data trying to be inserted.
        # We overwrite everything EXCEPT the unique keys and the creation timestamp.
        update_dict = {
            c.name: c
            for c in stmt.excluded
            if c.name not in unique_cols and c.name != "created_at"
        }

        # Attach the ON CONFLICT DO UPDATE clause
        if update_dict:
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=unique_cols, set_=update_dict
            )
        else:
            # Fallback just in case a table has no updatable columns
            upsert_stmt = stmt.on_conflict_do_nothing(index_elements=unique_cols)

        conn.execute(upsert_stmt)


def clean_rail_segments(data_list):
    """Parses stringified JSON arrays back into Python lists."""
    for row in data_list:
        if "trains_present" in row and isinstance(row["trains_present"], str):
            try:
                row["trains_present"] = json.loads(row["trains_present"])
            except json.JSONDecodeError:
                pass
    return data_list


if __name__ == "__main__":
    time.sleep(5)
    consume_and_store()
