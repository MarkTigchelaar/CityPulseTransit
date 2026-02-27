from copy import deepcopy
from src.simulation.domain.travel_plan import TravelPlan
from src.simulation.domain.route import Route
from src.simulation.entities.world_clock import WorldClock
from src.simulation.data_streams.system_event_bus import SystemEventBus


class Passenger:
    def __init__(
        self,
        passenger_id,
        travel_plans: list[TravelPlan],
        world_clock: WorldClock,
        system_event_bus: SystemEventBus,
        visited_station_ids: list[int],
    ):
        self.passenger_id = int(passenger_id)
        self.travel_plans = travel_plans
        self.is_travelling = False
        self.clock = world_clock
        self.current_route: Route = None
        self.visited_station_ids = visited_station_ids
        self.system_event_bus = system_event_bus

    def ready_to_start_travelling(self) -> bool:
        travel_day = self.clock.get_day_of_week()
        travel_hour = self.clock.get_hour()
        travel_minute = self.clock.get_minute()
        if self.is_travelling:
            return False
        matching_travel_plan = None
        for travel_plan in self.travel_plans:
            if travel_day.value not in travel_plan.travel_code.value:
                continue
            if travel_plan.start_arrival_hour != travel_hour:
                continue
            if travel_plan.start_arrival_minute != travel_minute:
                continue
            matching_travel_plan = travel_plan
            break
        if matching_travel_plan is None:
            return False

        self.current_route = matching_travel_plan.route
        return True

    def start_travelling(self) -> int:
        self.is_travelling = True
        return self.current_route.get_station_ids()[0]

    def is_in_system(self) -> bool:
        return self.is_travelling

    def resume_travelling(self) -> None:
        travel_day = self.clock.get_day_of_week()
        current_time = (self.clock.get_hour(), self.clock.get_minute())

        valid_plans = [
            p for p in self.travel_plans if travel_day.value in p.travel_code.value
        ]
        valid_plans.sort(key=lambda p: (p.start_arrival_hour, p.start_arrival_minute))
        for plan in reversed(valid_plans):
            plan_time = (plan.start_arrival_hour, plan.start_arrival_minute)
            if plan_time <= current_time:
                self.current_route = plan.route
                self.is_travelling = True
                return
        raise Exception(
            f"Passenger {self.passenger_id} could not find a past travel plan to resume."
        )

    def stop_travelling(self) -> None:
        self.current_route = None
        self.visited_station_ids = []
        self.is_travelling = False

    def get_id(self) -> int:
        return self.passenger_id

    def record_station_visit(self, current_station_id: int) -> None:
        self.visited_station_ids.append(current_station_id)

    def is_on_last_stop(self) -> bool:
        return self.current_route.is_route_complete(self.visited_station_ids)

    def get_next_station_id_on_route(self, station_id: int) -> int:
        return self.current_route.get_next_station_id(
            self.visited_station_ids, station_id
        )

    def log_station_entry(self, station_id: int, train_id: int = None) -> None:
        self._log_passenger_travelling_state(station_id, train_id)

    def log_station_exit(self, station_id: int, train_id: int = None) -> None:
        self._log_passenger_travelling_state(station_id, train_id)

    def _log_passenger_travelling_state(self, station_id: int, train_id: int = None) -> None:
        state = {
            "passenger_id": self.passenger_id,
            "clock_tick": self.clock.get_current_clock_tick(),
            "station_id": station_id,
            "train_id": train_id,
            "stops_seen_so_far": deepcopy(self.visited_station_ids),
        }
        self.system_event_bus.log_passenger_travelling_state(state)
