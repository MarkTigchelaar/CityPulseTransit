import json
from typing import Any
from collections import defaultdict
from abc import ABC, abstractmethod
from kafka import KafkaProducer
#from enum import Enum

class Producer(ABC):
    @abstractmethod
    def train_location_update(self, state):
        raise NotImplementedError

    @abstractmethod
    def train_state(self, state: dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def rail_segment_state(self, state: dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def platform_state(self, state: dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def station_state(self, state: dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def passenger_travelling_state(self, state: dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def world_clock_state(self, state: dict[str, Any]):
        raise NotImplementedError
    
    @abstractmethod
    def user_adjustable_variables_state(self, state: dict[str, Any]):
        raise NotImplementedError


class DummyProducer(Producer):
    def train_location_update(self, state):
        pass

    def train_state(self, state: dict[str, Any]):
        pass

    def rail_segment_state(self, state: dict[str, Any]):
        pass

    def platform_state(self, state: dict[str, Any]):
        pass

    def station_state(self, state: dict[str, Any]):
        pass

    def passenger_travelling_state(self, state: dict[str, Any]):
        pass

    def world_clock_state(self, state: dict[str, Any]):
        pass

    def user_adjustable_variables_state(self, state: dict[str, Any]):
        pass


class MemoryProducer(Producer):
    def __init__(self):
        self.events = defaultdict(list)

    def train_location_update(self, state):
        self.events["train_location"].append(state)  

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


class LiveProducer(Producer):
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
    

    def train_location_update(self, state):
        self.producer.send('train_location', value=state)
    def train_state(self, state: dict[str, Any]):
        self.producer.send('train_status', value=state)

    def rail_segment_state(self, state: dict[str, Any]):
        self.producer.send('rail_segments', value=state)

    def platform_state(self, state: dict[str, Any]):
        self.producer.send('platform_status', value=state)

    def station_state(self, state: dict[str, Any]):
        self.producer.send('station_status', value=state)

    def passenger_travelling_state(self, state: dict[str, Any]):
        self.producer.send('passenger_status', value=state)

    def world_clock_state(self, state: dict[str, Any]):
        self.producer.send('world_clock', value=state)

    def user_adjustable_variables_state(self, state: dict[str, Any]):
        self.producer.send('user_adjustable_variables', value=state)