from typing import Any
from collections import defaultdict
from simulation.producer import Producer


class MemoryProducer(Producer):
    def __init__(self):
        self.events = defaultdict(list)

    def train_state(self, state: dict[str, Any]):
        self.events["train_state"].append(state)

    def rail_segment_state(self, state: dict[str, Any]):
        self.events["rail_segment_state"].append(state)

    def platform_state(self, state: dict[str, Any]):
        self.events["platform_state"].append(state)

    def station_state(self, state: dict[str, Any]):
        self.events["station_state"].append(state)

    def passenger_travelling_state(self, state: dict[str, Any]):
        self.events["passenger_travelling_state"].append(state)

    def world_clock_state(self, state: dict[str, Any]):
        self.events["world_clock_state"].append(state)

    def get_events(self, topic: str):
        return self.events[topic]

    def clear(self):
        self.events.clear()
