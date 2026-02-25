import json
from typing import Any
from kafka import KafkaProducer
from simulation.producer import Producer

class LiveProducer(Producer):
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=["localhost:9092"],
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )

    def train_state(self, state: dict[str, Any]):
        self.producer.send("train_status", value=state)

    def rail_segment_state(self, state: dict[str, Any]):
        self.producer.send("rail_segments", value=state)

    def platform_state(self, state: dict[str, Any]):
        self.producer.send("platform_status", value=state)

    def station_state(self, state: dict[str, Any]):
        self.producer.send("station_status", value=state)

    def passenger_travelling_state(self, state: dict[str, Any]):
        self.producer.send("passenger_status", value=state)

    def world_clock_state(self, state: dict[str, Any]):
        self.producer.send("world_clock", value=state)
