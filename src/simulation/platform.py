from simulation.platform_state import PlatformState
from simulation.passenger import Passenger
from simulation.train import Train
from simulation.system_event_bus import SystemEventBus


# A station has a Platform for each route.
# This defines the stations capacity for trains at a given time
class Platform:
    def __init__(
        self,
        station_name,
        route_id: int,
        station_id: int,
        platform_state: PlatformState,
        train: Train,
        system_event_bus: SystemEventBus,
    ):
        self.name = station_name + f"({station_id})_route_" + str(route_id)
        self.route_id = route_id
        self.present_train = train
        self.station_id = station_id
        self.platform_state = platform_state
        self.system_event_bus = system_event_bus

    def get_route_id(self) -> int:
        return self.route_id

    def has_train(self) -> bool:
        return self.present_train is not None

    def current_train_id(self) -> int:
        if self.has_train():
            return self.present_train.get_id()
        return None

    def current_train_passenger_count(self) -> int:
        if self.has_train():
            return self.present_train.passenger_count()
        return 0

    def add_train(self, train: Train):
        # Protect trains from being disappeared
        if self.platform_state != PlatformState.Empty:
            raise Exception(
                f"Platform for route {self.route_id} in station {self.station_id} is in invalid state for train arrival: {self.platform_state}"
            )
        self.present_train = train
        self.present_train.add_to_stops_seen_so_far(self.station_id)
        self.platform_state = PlatformState.TrainArriving
        self.log_train_state()


    def log_train_state(self):
        if self.has_train():
            self.present_train.produce_state(
                station_id=self.station_id, segment_id=None
            )

    def update_states(self):
        if self.platform_state == PlatformState.MovingPassengers:
            self.platform_state = PlatformState.TrainDeparting
        elif self.platform_state == PlatformState.TrainArriving:
            self.platform_state = PlatformState.MovingPassengers

    def cannot_take_passengers(self) -> bool:
        return self.platform_state != PlatformState.MovingPassengers

    def embark_passenger(self, passenger: Passenger):
        passenger.log_station_exit(self.station_id, self.present_train.get_id())
        self.present_train.embark_passenger(passenger)

    def disembark_passengers(self) -> list[Passenger]:
        if not self.has_train():
            return []
        if self.platform_state != PlatformState.MovingPassengers:
            return []
        disembarked_passengers = self.present_train.disembark_passengers(
            self.station_id
        )
        self.log_train_state()
        return disembarked_passengers

    def train_ready_for_departure(self) -> bool:
        return self.platform_state == PlatformState.TrainDeparting

    def remove_train(self) -> Train:
        self.platform_state = PlatformState.Empty
        train = self.present_train
        self.present_train = None
        return train

    def get_trains_next_station_id(self) -> int:
        return self.present_train.get_next_station_id_on_route(self.station_id)

    def train_is_full(self) -> bool:
        if self.has_train():
            return self.present_train.at_capacity()
        return True

    def produce_state(self, current_clock_tick: int):
        state = {
            "station_id": self.station_id,
            "clock_tick": current_clock_tick,
            "route_id": self.route_id,
            "platform_state": self.platform_state.value,
        }
        self.system_event_bus.log_platform_state(state)

