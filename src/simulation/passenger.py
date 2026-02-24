from simulation.travel_plan import TravelPlan
from simulation.route import Route
from simulation.world_clock import WorldClock
from simulation.system_event_bus import SystemEventBus


class Passenger:
    def __init__(
        self,
        id,
        travel_plans: list[TravelPlan],
        world_clock: WorldClock,
        system_event_bus: SystemEventBus,
        stops_so_far: list[int],
    ):
        self.id = int(id)
        self.travel_plans = travel_plans
        self.is_travelling = False
        self.clock = world_clock
        self.current_route: Route = None
        self.station_ids_visited = stops_so_far
        self.system_event_bus = system_event_bus

    def ready_to_start_travelling(self) -> bool:
        travel_day = self.clock.get_day_of_week()
        travel_hour = self.clock.get_hour()
        travel_minute = self.clock.get_minute()
        if self.is_travelling:
            return False
        correct_travel_plan = None
        for travel_plan in self.travel_plans:
            if travel_day.value not in travel_plan.travel_code.value:
                continue
            if travel_plan.start_arrival_hour != travel_hour:
                continue
            if travel_plan.start_arrival_minute != travel_minute:
                continue
            correct_travel_plan = travel_plan
            break
        if correct_travel_plan is None:
            return False

        self.current_route = correct_travel_plan.route
        return True

    def start_travelling(self) -> int:
        self.is_travelling = True
        return self.current_route.get_station_ids()[0]

    def is_in_system(self) -> bool:
        return self.is_travelling

    def stop_travelling(self):
        self.current_route = None
        self.station_ids_visited = []
        self.is_travelling = False

    def get_id(self) -> int:
        return self.id

    def add_to_stops_seen_so_far(self, current_station_id: int):
        self.station_ids_visited.append(current_station_id)

    def on_last_stop(self) -> bool:
        return self.current_route.route_complete(self.station_ids_visited)

    def get_next_station_id_on_route(self, station_id: int) -> int:
        return self.current_route.get_next_station_id(
            self.station_ids_visited, station_id
        )

    def log_station_entry(self, station_id: int, train_id: int = None):
        self._log_passenger_travelling_state(station_id, train_id)

    def log_station_exit(self, station_id: int, train_id: int = None):
        self._log_passenger_travelling_state(station_id, train_id)

    def _log_passenger_travelling_state(
        self, station_id: int, train_id: int = None
    ):
        state = {
            "passenger_id": self.id,
            "clock_tick": self.clock.get_current_clock_tick(),
            "station_id": station_id,
            "train_id": train_id,
            "stops_seen_so_far": "{" + ",".join(map(str, self.station_ids_visited)) + "}"
        }
        self.system_event_bus.log_passenger_travelling_state(state)
