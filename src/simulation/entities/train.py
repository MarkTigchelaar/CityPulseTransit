from copy import deepcopy
from src.simulation.entities.world_clock import WorldClock
from src.simulation.entities.passenger import Passenger
from src.simulation.domain.route import Route
from src.simulation.data_streams.system_event_bus import SystemEventBus


class Train:
    def __init__(
        self,
        train_id,
        route: Route,
        ordering: int,
        capacity: int,
        clock: WorldClock,
        passengers: list[Passenger],
        station_ids_visited: list[int],
        system_event_bus: SystemEventBus,
    ):
        self.train_id = train_id
        self.route = route
        self.ordering = ordering
        self.capacity = capacity
        self.passengers = {passenger.get_id(): passenger for passenger in passengers}
        self.clock = clock
        self.system_event_bus = system_event_bus
        self.station_ids_visited = station_ids_visited

    def embark_passenger(self, passenger: Passenger) -> None:
        if self.at_capacity():
            raise Exception("Attempted to add passenger to train, when full")

        self.passengers[passenger.get_id()] = passenger

    def disembark_passengers(self, current_station_id: int) -> list[Passenger]:
        passengers_to_disembark = []
        next_stop = self.get_next_station_id_on_route(current_station_id)
        for passenger in self.passengers.values():
            if passenger.is_on_last_stop():
                passengers_to_disembark.append(passenger)
            elif (
                passenger.get_next_station_id_on_route(current_station_id) != next_stop
            ):
                passengers_to_disembark.append(passenger)
        for passenger in passengers_to_disembark:
            self.passengers.pop(passenger.get_id())
        return passengers_to_disembark

    def get_id(self) -> int:
        return self.train_id

    def get_route_id(self) -> int:
        return self.route.get_id()

    def get_ordering(self) -> int:
        return self.ordering

    def at_capacity(self) -> bool:
        return len(self.passengers) >= self.capacity

    def passenger_count(self) -> int:
        return len(self.passengers)

    def is_on_last_stop(self) -> bool:
        return self.route.is_route_complete(self.station_ids_visited)

    def reset_route(self) -> None:
        self.station_ids_visited = [self.route.get_station_ids()[0]]

    def record_station_visit(self, current_station_id: int) -> None:
        self.station_ids_visited.append(current_station_id)
        for passenger_id in self.passengers:
            self.passengers[passenger_id].record_station_visit(current_station_id)

    def get_next_station_id_on_route(self, current_station_id: int) -> int:
        next_station_id = self.route.get_next_station_id(
            self.station_ids_visited, current_station_id
        )
        if next_station_id is not None:
            return next_station_id
        if self.route.is_route_complete(self.station_ids_visited):
            self.reset_route()
            return self.route.get_station_ids()[1]
        else:
            raise Exception("Train in unknown invalid state")

    def produce_state(self, station_id: int = None, segment_id: int = None) -> None:
        state = {
            "train_id": self.train_id,
            "clock_tick": self.clock.get_current_clock_tick(),
            "station_id": station_id,
            "segment_id": segment_id,
            "stops_seen_so_far": deepcopy(self.station_ids_visited),
            "passenger_count": self.passenger_count(),
        }
        self.system_event_bus.log_train_state(state)
