from copy import deepcopy
from simulation.world_clock import WorldClock
from simulation.passenger import Passenger
from simulation.route import Route
from simulation.system_event_bus import SystemEventBus


class Train:
    def __init__(
        self,
        id,
        route: Route,
        ordering: int,
        capacity: int,
        clock: WorldClock,
        passengers: list[Passenger],
        stops_seen_so_far: list[int],
        system_event_bus: SystemEventBus,
    ):
        self.id = id
        self.route = route
        self.ordering = ordering
        self.capacity = capacity
        self.passengers = {passenger.get_id(): passenger for passenger in passengers}
        self.clock = clock
        self.system_event_bus = system_event_bus
        self.station_ids_visited = stops_seen_so_far

    def embark_passenger(self, passenger: Passenger):
        if self.at_capacity():
            raise Exception("Attempted to add passenger to train, when full")

        self.passengers[passenger.get_id()] = passenger

    def disembark_passengers(self, current_station_id: int) -> list[Passenger]:
        passengers_to_disembark = []
        next_stop = self.get_next_station_id_on_route(current_station_id)
        for passenger in self.passengers.values():
            if passenger.on_last_stop():
                passengers_to_disembark.append(passenger)
            elif (
                passenger.get_next_station_id_on_route(current_station_id) != next_stop
            ):
                passengers_to_disembark.append(passenger)
        for passenger in passengers_to_disembark:
            self.passengers.pop(passenger.get_id())
        return passengers_to_disembark

    def get_id(self) -> int:
        return self.id

    def get_route_id(self) -> int:
        return self.route.get_id()

    def get_ordering(self) -> int:
        return self.ordering

    def at_capacity(self) -> bool:
        return len(self.passengers) >= self.capacity

    def passenger_count(self) -> int:
        return len(self.passengers)

    def on_last_stop(self) -> bool:
        return self.route.route_complete(self.station_ids_visited)

    def reset_route(self):
        self.station_ids_visited = [self.route.get_station_ids()[0]]

    def add_to_stops_seen_so_far(self, current_station_id: int):
        self.station_ids_visited.append(current_station_id)
        for passenger_id in self.passengers:
            self.passengers[passenger_id].add_to_stops_seen_so_far(current_station_id)

    def get_next_station_id_on_route(self, station_id: int) -> int:
        next_station_id = self.route.get_next_station_id(
            self.station_ids_visited, station_id
        )
        if next_station_id is not None:
            return next_station_id
        if self.route.route_complete(self.station_ids_visited):
            self.reset_route()
            return self.route.get_station_ids()[1]
        else:
            raise Exception("Train in unknown invalid state")

    def produce_state(self, station_id: int = None, segment_id: int = None):
        state = {
            "train_id": self.id,
            "clock_tick": self.clock.get_current_clock_tick(),
            "station_id": station_id,
            "segment_id": segment_id,
            "stops_seen_so_far": deepcopy(self.station_ids_visited),
            "passenger_count": self.passenger_count(),
        }
        self.system_event_bus.log_train_state(state)
