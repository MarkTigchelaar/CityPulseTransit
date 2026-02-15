from simulation.constants import PlatformState
from simulation.world_clock import WorldClock
from simulation.passenger import Passenger
from simulation.train import Train
from simulation.rail_segment import RailSegment
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
        self.log_train_state()
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


class Station:
    def __init__(
        self,
        station_id: int,
        station_name: str,
        clock: WorldClock,
        passengers: list[Passenger],
        trains: list[Train],
        incoming_segments: list[RailSegment],
        outgoing_segments: list[RailSegment],
        platform_states: dict[int, PlatformState],
        system_event_bus: SystemEventBus,
    ):
        self.id = int(station_id)
        self.name = station_name
        self.passengers = passengers
        self.incoming_segments = incoming_segments
        self.outgoing_segments_lookup = {
            segment.get_station_ids()["to"]: segment for segment in outgoing_segments
        }
        self.system_event_bus = system_event_bus
        self.platforms = []
        self.configure_platforms(platform_states, trains)
        self.clock = clock
        self.passengers_boarded_trains = 0
        self.passengers_entered_station = 0


    def get_id(self) -> int:
        return self.id

    def configure_platforms(
        self, platform_states: dict[int, PlatformState], trains: list[Train]
    ):
        for route_id in platform_states:
            trains_for_platform = []
            train_on_platform = None
            for train in trains:
                if train.get_route_id() == route_id:
                    trains_for_platform.append(train)
            number_of_available_trains = len(trains_for_platform)

            if number_of_available_trains > 1:
                raise Exception(
                    f"Multiple trains for platform on route {route_id} in station {self.id}"
                )
            elif number_of_available_trains == 1:
                train_on_platform = trains_for_platform[0]
            platform_state = platform_states[route_id]
            platform = Platform(
                self.name,
                route_id,
                self.id,
                platform_state,
                train_on_platform,
                self.system_event_bus,
            )
            self.platforms.append(platform)

    def process(self):
        self._accept_incoming_trains()
        self._disembark_passengers()
        self._process_finished_passengers()
        self._embark_passengers()
        self._depart_trains()
        self._mark_trains_as_ready_for_next_action()
        self._log_current_traffic()

    def _accept_incoming_trains(self):
        for platform in self.platforms:
            route_id = platform.get_route_id()
            if platform.has_train():
                continue
            for rail_segment in self.incoming_segments:
                if not rail_segment.has_trains():
                    continue
                if not rail_segment.train_at_end_of_segment():
                    continue
                train_route_id = rail_segment.get_next_train_route_id()
                if train_route_id == route_id:
                    next_train = rail_segment.train_departure()
                    platform.add_train(next_train)
                    break

    def _disembark_passengers(self):
        for platform in self.platforms:
            for arrived_passenger in platform.disembark_passengers():
                arrived_passenger.log_station_entry(
                    self.id, platform.current_train_id()
                )
                self.passenger_enter_station(arrived_passenger, entering_system=False)
                self.passengers_entered_station += 1

    def _embark_passengers(self):
        for platform in self.platforms:
            embarked_passengers = []
            if not platform.has_train():
                continue
            if platform.cannot_take_passengers():
                continue
            trains_next_stop = platform.get_trains_next_station_id()
            for passenger in self.passengers:
                if platform.train_is_full():
                    break
                passenger_next_stop = passenger.get_next_station_id_on_route(self.id)
                if passenger_next_stop is None:
                    continue
                if trains_next_stop == passenger_next_stop:
                    embarked_passengers.append(passenger)
                    platform.embark_passenger(passenger)

            self.passengers_boarded_trains += len(embarked_passengers)
            for passenger in embarked_passengers:
                self.passengers.remove(passenger)

    def _process_finished_passengers(self):
        passengers_done_travelling = []
        for passenger in self.passengers:
            if passenger.on_last_stop():
                passengers_done_travelling.append(passenger)
        for passenger in passengers_done_travelling:
            self.passengers.remove(passenger)
            passenger.log_station_exit(self.id)
            passenger.stop_travelling()

    def passenger_enter_station(
        self, passenger: Passenger, entering_system: bool = True
    ):
        id = passenger.get_id()
        if id in self.passengers:
            raise Exception(f"Passenger {id} in station {self.name} already!")
        if entering_system:
            passenger.add_to_stops_seen_so_far(self.id)
            passenger.log_station_entry(self.id)
        self.passengers.append(passenger)

    def _depart_trains(self):
        for platform in self.platforms:
            if not platform.has_train():
                continue
            if platform.train_ready_for_departure():
                next_station_id = platform.get_trains_next_station_id()
                if next_station_id not in self.outgoing_segments_lookup:

                    raise Exception(
                        f"Outgoing train attempting to go station {next_station_id} from {self.name}:{self.id}, but no connection exists from station"
                    )
                rail_segment = self.outgoing_segments_lookup[next_station_id]
                if rail_segment.can_take_another_train():
                    train = platform.remove_train()
                    rail_segment.train_arrival(train)

    def _mark_trains_as_ready_for_next_action(self):
        for platform in self.platforms:
            platform.update_states()

    def _log_current_traffic(self):
        passengers_in_trains = 0
        trains_at_platforms = []
        for platform in self.platforms:
            platform.produce_state(self.clock.get_current_clock_tick())
            passengers_in_trains += platform.current_train_passenger_count()
            if platform.has_train():
                trains_at_platforms.append(
                    {
                        "id": platform.current_train_id(),
                        "position": platform.get_route_id(),
                    }
                )
        passengers_waiting = len(self.passengers)
        total_passengers_in_station = passengers_in_trains + passengers_waiting
        state = {
            "station_id": self.id,
            "clock_tick": self.clock.get_current_clock_tick(),
            "total_passengers_in_station": total_passengers_in_station,
            "passengers_boarded_trains": self.passengers_boarded_trains,
            "passengers_entered_station": self.passengers_entered_station,
            "passengers_waiting": passengers_waiting,
        }
        self.system_event_bus.log_station_state(state)
        self.system_event_bus.log_train_location_state(
            {
                "station_id": self.id,
                "clock_tick": self.clock.get_current_clock_tick(),
                "trains_present": trains_at_platforms,
                "segment_id": None,
                "station_id": self.id
            }
        )
        self.passengers_boarded_trains = 0
        self.passengers_entered_station = 0
