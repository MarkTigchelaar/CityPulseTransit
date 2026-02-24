import json
import time
from kafka import KafkaConsumer
from sqlalchemy import create_engine, exc
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, INTEGER
import pandas as pd
import uuid
from copy import copy

# --- Configuration ---
# Map Kafka Topics to landing tables
TOPIC_MAPPING = {
    
    "station_status": "station_passenger_stats",
    "rail_segments": "runtime_rail_segment_state", 
    "platform_status": "runtime_platform_state",
    "world_clock": "runtime_world_clock_state",
    "passenger_travelling_state": "runtime_passenger_state",
    "station_status": "station_passenger_stats",
    "train_status": "runtime_train_state",
}

BATCH_SIZE = 1
DB_CONNECTION = "postgresql://thomas:mind_the_gap@localhost:5432/subway_system"

def get_db_engine():
    return create_engine(DB_CONNECTION)

def consume_and_store():
    topics = list(TOPIC_MAPPING.keys())
    print(f"Connecting to Kafka topics: {topics}...")
    
    consumer = KafkaConsumer(
        *topics,  # Unpack the list to subscribe to all of them
        bootstrap_servers=['localhost:9092'],
        group_id=f'transit_group',
        auto_offset_reset='earliest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    engine = get_db_engine()
    buffers = {topic: [] for topic in topics}

    print("Consumer started. Waiting for data...")
    
    for message in consumer:
        topic = message.topic
        data = message.value
        if topic in buffers:
            buffers[topic].append(data)
            if len(buffers[topic]) >= BATCH_SIZE:
                target_table = TOPIC_MAPPING[topic]
                insert_batch(engine, buffers[topic], target_table)
                buffers[topic] = []

def insert_batch(db_engine, data_list, table_name):
    if not data_list:
        return
        
    #try:
    with db_engine.begin() as conn:
        df = pd.DataFrame(data_list)
        df.to_sql(table_name, conn, 
                    if_exists='append', 
                    schema="public_transit", 
                    index=False)
    # except exc.SQLAlchemyError as e:
    #     print(f"\n❌ TRUE DB ERROR inserting into {table_name}:\n{e}\n")
    # except Exception as e:
    #     print(f"\n❌ GENERAL ERROR inserting into {table_name}:\n{e}\n")


    
if __name__ == "__main__":
    time.sleep(5) 
    consume_and_store()