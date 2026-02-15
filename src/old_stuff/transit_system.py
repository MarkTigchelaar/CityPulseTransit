import time
import random
from producer import TempProducer
from table_data_reader import TableDataReader
class TempTransitSystem:
    def __init__(self):
        self.producer = TempProducer()
        self.clock_tick = 0

    def run(self):
        print("Transit System Started... Press Ctrl+C to stop.")
        while True:
            self.send_world_clock_state()
            self.send_passenger_state()
            self.send_train_state()
            self.send_segment_state()
            self.send_platform_state()
            self.send_station_state()
            self.send_user_adjustable_variables_state()

            time.sleep(1)
            self.clock_tick += 1
            print(f"Tick: {self.clock_tick} | Data sent to Kafka")

    def send_passenger_state(self):
        state = {
            "passenger_id": random.randint(1, 100),
            "clock_tick": self.clock_tick,
            "station_id": random.randint(1, 3),
            "train_id": random.randint(1, 5),
            "status": random.choice(["arriving", "departing"]),
        }
        self.producer.passenger_travelling_state(state)

    def send_train_state(self):
        state = {
            "train_id": random.randint(100, 120),
            "clock_tick": self.clock_tick,
            "station_id": random.randint(1, 3),
            "segment_id": random.randint(1, 20),
            "number_of_stops_seen": random.randint(0, 10),
            "passenger_count": random.randint(0, 10)
        }
        self.producer.train_state(state)

    def send_segment_state(self):
        state = {
            "segment_id": random.randint(1, 20),
            "clock_tick": self.clock_tick,
            "trains_present": [
                {
                    "id": 1,
                    "position": 1.2
                },
                {
                    "id": 2, 
                    "position": 1.2
                },
                {
                    "id": 3,
                    "position": 1.3
                }
            ],
            
        }
        self.producer.rail_segment_state(state)
    
    def send_platform_state(self):
        state = {
            "station_id": random.randint(1, 3),
            "clock_tick": self.clock_tick,
            "route_id": random.randint(1, 5),
            "platform_state": random.choice(["Empty", "Arrival", "MovingPassengers", "Departure"]),
        }
        self.producer.platform_state(state)

    def send_station_state(self):
        state = {
            "station_id": random.randint(1, 3),
            "clock_tick": self.clock_tick,
            "total_passengers_in_station": random.randint(0, 200),
            "passengers_boarded_trains": random.randint(0, 20),
            "passengers_entered_station": random.randint(0, 20),
            "passengers_waiting": random.randint(0, 50),
            "trains_at_platform": random.randint(0, 2),
        }
        self.producer.station_state(state)
    
    def send_world_clock_state(self):
        state = {
            "clock_tick": self.clock_tick,
            "day_of_week": random.choice(['M', 'T', 'W', 'R', 'F', 'S', 'U']),
            "hour_of_day": random.randint(6, 22),
            "minute": random.randint(0, 59),
        }
        self.producer.world_clock_state(state)

    def send_user_adjustable_variables_state(self):
        state = {
            "clock_tick": self.clock_tick,
            "clock_rate": 5.0,
            "train_speed": 50.0
        }
        self.producer.user_adjustable_variables_state(state)

if __name__ == "__main__":
    table_state_reader = TableDataReader()
    trains_df = table_state_reader.read_train_runtime_state()
    print("Sample Train State Data:")
    print(trains_df.head())
    system = TempTransitSystem()
    system.run()
