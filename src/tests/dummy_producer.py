from typing import Any
from simulation.producer import Producer


class DummyProducer(Producer):

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
