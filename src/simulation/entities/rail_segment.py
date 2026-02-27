from collections import deque
from src.simulation.entities.train import Train
from src.simulation.entities.world_clock import WorldClock
from src.simulation.data_streams.system_event_bus import SystemEventBus
from src.simulation.domain.platform_state import TRAIN_LIMIT_PER_SEGMENT


class _TrainWithLocation:
    def __init__(
        self,
        train: Train,
        position_km: float,
        distance_km: float,
        segment_id: int,
        speed_km_per_tick: float,
    ):
        self.train = train
        self.position_km = position_km
        self.distance_km = distance_km
        self.segment_id = segment_id
        self.speed_km_per_tick = speed_km_per_tick

    def get_position(self) -> float:
        return int(self.position_km * 1000) / 1000.0

    def move(self) -> None:
        self.position_km += self.speed_km_per_tick
        self.position_km = self.get_position()
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
        speed_km_per_tick: float,
        ordered_train_position_maps_in_segment: list[dict[str, Train | float]],
        system_event_bus: SystemEventBus,
        world_clock: WorldClock,
    ):
        self.id = int(segment_id)
        self.from_station_id = from_station_id
        self.to_station_id = to_station_id
        self.distance_km = float(distance_km)
        self.speed_km_per_tick = float(speed_km_per_tick)
        self.trains_in_segment = deque()

        # This enforces ordering
        for position_map in ordered_train_position_maps_in_segment:
            train = position_map["train"]
            position_km = position_map["position_km"]
            train_w_location = _TrainWithLocation(
                train, position_km, self.distance_km, self.id, self.speed_km_per_tick
            )
            self.trains_in_segment.append(train_w_location)
        self.system_event_bus = system_event_bus
        self.clock = world_clock

    def process(self) -> None:
        self._move_trains()
        state = self._make_current_segment_state()
        self.system_event_bus.log_rail_segment_state(state)

    def _make_current_segment_state(self) -> dict:
        return {
            "segment_id": self.get_id(),
            "clock_tick": self.clock.get_current_clock_tick(),
            "trains_present": self._make_train_position_records(),
        }

    def _make_train_position_records(self) -> list[dict]:
        return [
            {
                "id": train_w_location.train.get_id(),
                "position_km": train_w_location.get_position(),
            }
            for train_w_location in list(self.trains_in_segment)
        ]

    def _move_trains(self) -> None:
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

    def get_lead_train_route_id(self) -> int:
        if self.has_trains():
            return self.trains_in_segment[0].train.get_route_id()
        raise Exception("No trains on this segment")

    def is_lead_train_at_end(self) -> bool:
        if not self.has_trains():
            return False
        return self.trains_in_segment[0].get_position() >= self.distance_km

    def can_take_another_train(self) -> bool:
        return len(self.trains_in_segment) <= TRAIN_LIMIT_PER_SEGMENT

    def has_trains(self) -> bool:
        return len(self.trains_in_segment) > 0

    def accept_train(self, train: Train, position_km: float = 0.0) -> None:
        train_w_location = _TrainWithLocation(
            train, position_km, self.distance_km, self.id, self.speed_km_per_tick
        )
        self.trains_in_segment.append(train_w_location)

    def release_train(self) -> None:
        if self.has_trains() and self.is_lead_train_at_end():
            departing_train_w_location = self.trains_in_segment.popleft()
            return departing_train_w_location.train
        raise Exception(f"No trains to depart from this segment: {self.id}")
