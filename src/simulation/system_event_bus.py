from simulation.producer import Producer
from typing import Any


"""
Leaving some room for later developments.
For now, the SystemEventBus is a simple wrapper around the Producer, providing a clear interface for logging different types of events.
In the future, we could add features like:
- Event validation (ensuring required fields are present)
- Event transformation (enriching with additional data)
"""


class SystemEventBus:
    def __init__(self, producer: Producer):
        self.producer = producer

    def log_train_location_state(self, state: dict[str, Any]):
        self.producer.train_location_update(state)

    def log_train_state(self, state: dict[str, Any]):
        self.producer.train_state(state)

    def log_rail_segment_state(self, state: dict[str, Any]):
        self.producer.rail_segment_state(state)

    def log_platform_state(self, state: dict[str, Any]):
        self.producer.platform_state(state)

    def log_station_state(self, state: dict[str, Any]):
        self.producer.station_state(state)

    def log_passenger_travelling_state(self, state: dict[str, Any]):
        self.producer.passenger_travelling_state(state)

    def log_world_clock_state(self, state: dict[str, Any]):
        self.producer.world_clock_state(state)

    def log_user_adjustable_variables(self, state: dict[str, Any]):
        self.producer.user_adjustable_variables_state(state)
