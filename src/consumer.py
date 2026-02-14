import json
import time
from kafka import KafkaConsumer
from sqlalchemy import create_engine
import pandas as pd
import uuid
from copy import copy

# --- Configuration ---
# Map Kafka Topics to Database Table Names
TOPIC_MAPPING = {
    "train_status": "runtime_train_state",
    "station_status": "station_passenger_stats",
    "rail_segments": "runtime_rail_segment_state", 
    "platform_status": "runtime_platform_state",
    "user_adjustable_variables": "runtime_user_adjustable_variables_state",
    "world_clock": "runtime_world_clock_state"
}

BATCH_SIZE = 10
DB_CONNECTION = "postgresql://thomas:mind_the_gap@localhost:5432/subway_system"

def get_db_engine():
    return create_engine(DB_CONNECTION)

def consume_and_store():
    topics = list(TOPIC_MAPPING.keys())
    print(f"🔌 Connecting to Kafka topics: {topics}...")
    
    consumer = KafkaConsumer(
        *topics,  # Unpack the list to subscribe to all of them
        bootstrap_servers=['localhost:9092'],
        group_id=f'subway_group_{uuid.uuid4()}',
        auto_offset_reset='earliest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    engine = get_db_engine()
    
    # buffers is now a dict: {'train_status': [], 'station_status': [], ...}
    buffers = {topic: [] for topic in topics}

    print("🚀 Consumer started. Waiting for data...")
    
    for message in consumer:
        topic = message.topic  # <--- THIS IS THE KEY
        data = message.value
        
        # 1. Add to the specific buffer for this topic
        if topic in buffers:
            buffers[topic].append(data)

            # 2. Check if THIS specific buffer is full
            if len(buffers[topic]) >= BATCH_SIZE:
                unpack_lists(buffers, topic)
                target_table = TOPIC_MAPPING[topic]
                insert_batch(engine, buffers[topic], target_table)
                buffers[topic] = []  # Clear just this buffer

def insert_batch(engine, data_list, table_name):
    if not data_list:
        return

    try:
        with engine.connect() as conn:
            df = pd.DataFrame(data_list)
            
            # Using the dynamic table_name passed in
            df.to_sql(table_name, conn, 
                      if_exists='append', 
                      schema="public_transit", 
                      index=False)
            
            print(f"✅ Inserted {len(data_list)} records into {table_name}")
            
    except Exception as e:
        print(f"❌ Error inserting into {table_name}: {e}")


def unpack_lists(buffers, topic):
    if topic != 'rail_segments':
        return 
    segment_rows = buffers[topic]
    unpacked_rows = []
    for row in segment_rows:
        trains_present = row["trains_present"]
        if len(trains_present) < 1:
            row.pop("trains_present")
            row["train_id"] = None
            row["train_position"] = None
            row["train_queuing_order"] = None
            unpacked_rows.append(row)
            continue
        row.pop("trains_present")
        for i, train_map in enumerate(trains_present):
            copied_row = copy(row)
            copied_row["train_id"] = train_map["id"]
            copied_row["train_position"] = train_map["position"]
            copied_row["train_queuing_order"] = i
            unpacked_rows.append(copied_row)
    buffers[topic] = unpacked_rows

    
if __name__ == "__main__":
    time.sleep(5) 
    consume_and_store()