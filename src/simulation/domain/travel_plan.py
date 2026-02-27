from src.simulation.domain.travel_days import TravelDays
from src.simulation.domain.route import Route


class TravelPlan:
    def __init__(
        self,
        route: Route,
        start_arrival_hour: int,
        start_arrival_minute: int,
        travel_code: str,
    ):
        station_ids = route.get_station_ids()
        self.start_station_id = station_ids[0]
        self.end_station_id = station_ids[-1]
        self.start_arrival_hour = start_arrival_hour
        self.start_arrival_minute = start_arrival_minute
        self.travel_code = TravelDays.from_code(travel_code)
        self.route = route

    def get_route(self) -> Route:
        return self.route

    def __repr__(self) -> str:
        return f"TravelPlan(from: {self.start_station_id}, at: {self.start_arrival_hour} to: {self.end_station_id}, days: {self.travel_code})"
