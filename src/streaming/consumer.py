import json
import time
from typing import Any
from kafka import KafkaConsumer
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from src.config import DB_CONNECTION, KAFKA_BROKER_PORT, HOST_NAME


TOPIC_MAPPING = {
    "station_status": "station_passenger_stats",
    "rail_segments": "runtime_rail_segment_state",
    "platform_status": "runtime_platform_state",
    "world_clock": "runtime_world_clock_state",
    "passenger_status": "runtime_passenger_state",
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


def make_topic_list() -> list[str]:
    return list(TOPIC_MAPPING.keys())


def generate_buffer() -> dict[str, Any]:
    return {topic: [] for topic in make_topic_list()}


def get_db_engine():
    return create_engine(DB_CONNECTION)


def consume_and_store():
    topics = make_topic_list()
    print(f"Connecting to Kafka topics: {topics}...")

    # NOTE: Data recovery strategy
    # I use a static 'group.id' here so the consumer resumes exactly where
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
        bootstrap_servers=[HOST_NAME + ":" + KAFKA_BROKER_PORT],
        group_id="transit_group",
        auto_offset_reset="earliest",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    engine = get_db_engine()
    metadata = MetaData(schema="public_transit")

    print("Consumer started. Waiting for data...")
    data_buffer = generate_buffer()
    for message in consumer:
        topic = message.topic
        data = message.value

        if topic not in data_buffer:
            raise KeyError(f"Consumer topic key {topic} is invalid")

        if topic == "world_clock":
            insert_batch(engine, data_buffer, metadata)
            data_buffer = generate_buffer()
        data_buffer[topic].append(data)


def insert_batch(db_engine, data_buffer, metadata):
    for topic in data_buffer:
        data_list = data_buffer[topic]
        table_name = TOPIC_MAPPING[topic]
        insert_topic(db_engine, data_list, metadata, table_name)


def insert_topic(db_engine, data_list, metadata, table_name):
    if not data_list:
        return

    with db_engine.begin() as conn:
        table = Table(table_name, metadata, autoload_with=db_engine)
        stmt = insert(table).values(data_list)
        unique_cols = TABLE_UNIQUE_KEYS[table_name]
        update_dict = {
            c.name: c
            for c in stmt.excluded
            if c.name not in unique_cols and c.name != "created_at"
        }

        if update_dict:
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=unique_cols, set_=update_dict
            )
        else:
            upsert_stmt = stmt.on_conflict_do_nothing(index_elements=unique_cols)

        conn.execute(upsert_stmt)


if __name__ == "__main__":
    time.sleep(5)
    consume_and_store()
