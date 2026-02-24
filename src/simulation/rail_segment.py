import json
from collections import deque
from simulation.train import Train
from simulation.world_clock import WorldClock
from simulation.system_event_bus import SystemEventBus
from simulation.constants import TRAIN_LIMIT_PER_SEGMENT


class TrainWithLocation:
    def __init__(
        self, train: int, position_km: float, distance_km: float, segment_id: int, speed: float
    ):
        self.train = train
        self.position_km = position_km
        self.distance_km = distance_km
        self.segment_id = segment_id
        self.speed = speed

    def get_position(self) -> float:
        return int(self.position_km * 1000) / 1000.0

    def move(self):
        self.position_km += self.speed
        if self.position_km > self.distance_km:
            self.position_km = self.distance_km
        self.train.produce_state(station_id=None, segment_id=self.segment_id)


class RailSegment:
    def __init__(
        self,
        segment_id,
        from_station_id: int,
        to_station_id: int,
        distance_km: float,
        speed: float,
        ordered_train_position_maps_in_segment: list[dict[str, Train | float]],
        system_event_bus: SystemEventBus,
        world_clock: WorldClock,
    ):
        self.id = int(segment_id)
        self.from_station_id = from_station_id
        self.to_station_id = to_station_id
        self.distance_km = float(distance_km)
        self.speed = float(speed)
        self.trains_in_segment = deque()

        # This enforces ordering
        for position_map in ordered_train_position_maps_in_segment:
            train = position_map["train"]
            position_km = position_map["position_km"]
            train_w_location = TrainWithLocation(
                train, position_km, self.distance_km, self.id, self.speed
            )
            self.trains_in_segment.append(train_w_location)
        self.system_event_bus = system_event_bus
        self.clock = world_clock

    def process(self):
        self._move_trains()
        state = self._make_current_segment_state()
        self.system_event_bus.log_rail_segment_state(state)

    def _make_current_segment_state(self) -> dict:
        return {
            "segment_id": self.get_id(),
            "clock_tick": self.clock.get_current_clock_tick(),
            "trains_present": self._make_train_id_list(),
        }

    def _make_train_id_list(self) -> list[dict]:
        return [
            {
                "id": train_w_location.train.get_id(),
                "position_km": train_w_location.get_position(),
            }
            for train_w_location in list(self.trains_in_segment)
        ]

    def _move_trains(self):
        for train_w_location in list(self.trains_in_segment):
            train_w_location.move()

    def get_id(self) -> int:
        return self.id

    def count_trains(self) -> int:
        return len(self.trains_in_segment)

    def get_segment_length_km(self) -> float:
        return self.distance_km

    def get_station_ids(self) -> dict[str, int]:
        return {"from": self.from_station_id, "to": self.to_station_id}

    def get_next_train_route_id(self) -> int:
        if self.has_trains():
            return self.trains_in_segment[0].train.get_route_id()
        raise Exception("No trains on this segment")

    def train_at_end_of_segment(self) -> bool:
        if not self.has_trains():
            return False
        return self.trains_in_segment[0].get_position() >= self.distance_km

    def can_take_another_train(self) -> bool:
        return len(self.trains_in_segment) <= TRAIN_LIMIT_PER_SEGMENT

    def has_trains(self) -> bool:
        return len(self.trains_in_segment) > 0

    def train_arrival(self, train: Train, position_km: float = 0.0):
        train_w_location = TrainWithLocation(
            train, position_km, self.distance_km, self.id, self.speed
        )
        self.trains_in_segment.append(train_w_location)

    def train_departure(self):
        if self.has_trains() and self.train_at_end_of_segment():
            departing_train_w_location = self.trains_in_segment.popleft()
            return departing_train_w_location.train
        raise Exception(f"No trains to depart from this segment: {self.id}")
