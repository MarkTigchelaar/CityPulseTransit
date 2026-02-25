from typing import Any
from abc import ABC, abstractmethod


class Producer(ABC):

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
