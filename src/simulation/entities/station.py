from src.simulation.domain.platform_state import PlatformState
from src.simulation.entities.world_clock import WorldClock
from src.simulation.entities.passenger import Passenger
from src.simulation.entities.train import Train
from src.simulation.entities.rail_segment import RailSegment
from src.simulation.entities.platform import Platform
from src.simulation.data_streams.system_event_bus import SystemEventBus


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
        self.disembarked_passengers = []
        self.waiting_passengers = passengers
        self.incoming_segments = incoming_segments
        self.outgoing_segments_lookup = {
            segment.get_station_ids()["to"]: segment for segment in outgoing_segments
        }
        self.system_event_bus = system_event_bus
        self.platforms = []
        self.clock = clock
        self._configure_platforms(platform_states, trains)
        self.passengers_boarded_trains = 0
        self.passengers_entered_station = 0

    def get_id(self) -> int:
        return self.id

    def _configure_platforms(
        self, platform_states: dict[int, PlatformState], trains: list[Train]
    ) -> None:
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
                self.clock,
            )
            self.platforms.append(platform)

    def receive_passenger(self, new_passenger: Passenger) -> None:
        new_passenger.record_station_visit(self.id)
        new_passenger.log_passenger_travelling_state(self.id)
        self.waiting_passengers.append(new_passenger)

    def process(self) -> None:
        self._process_train_arrivals()
        self._move_passengers()
        self._process_train_departures()
        self._update_platform_states()
        self._log_current_traffic()

    def _process_train_arrivals(self) -> None:
        for platform in self.platforms:
            if not platform.platform_empty_state():
                continue
            if platform.has_train():
                raise Exception("Platform is not in empty state")
            for rail_segment in self.incoming_segments:
                if not rail_segment.has_trains():
                    continue
                if not rail_segment.is_lead_train_at_end():
                    continue
                train_route_id = rail_segment.get_lead_train_route_id()
                if train_route_id == platform.get_route_id():
                    next_train = rail_segment.release_train()
                    platform._process_train_arrivals(next_train)
                    # Empty -> TrainArriving
                    platform.update_state()
                    break

    def _move_passengers(self) -> None:
        disembarked_passengers = self._disembark_passengers()

        # Ensures freshly disembarked passengers
        # are processed after passengers that were already waiting
        self.waiting_passengers.extend(disembarked_passengers)
        finished_passengers = self._seperate_finished_passengers()
        boarded_passengers = self._board_passengers()
        for passenger in finished_passengers:
            passenger.log_passenger_travelling_state(
                station_id=self.get_id(), train_id=None
            )
            self.passengers_entered_station += 1
            passenger.stop_travelling()
        for passenger, train_id in boarded_passengers:
            passenger.log_passenger_travelling_state(station_id=None, train_id=train_id)
        for passenger in disembarked_passengers:
            if passenger in self.waiting_passengers:
                passenger.log_passenger_travelling_state(
                    station_id=self.get_id(), train_id=None
                )
                self.passengers_entered_station += 1

    def _seperate_finished_passengers(self) -> list[Passenger]:
        finished_passengers = []
        for passenger in self.waiting_passengers:
            if passenger.is_on_last_stop():
                finished_passengers.append(passenger)
        self._filter_waiting_passengers(finished_passengers)
        return finished_passengers

    def _filter_waiting_passengers(self, filter_list: list[Passenger]) -> None:
        id_list = [p.get_id() for p in filter_list]
        self.waiting_passengers = [
            passenger
            for passenger in self.waiting_passengers
            if passenger.get_id() not in id_list
        ]

    def _disembark_passengers(self) -> list[Passenger]:
        disembarked_passengers = []
        for platform in self.platforms:
            if not platform.can_move_passengers():
                continue
            disembarked_passengers.extend(platform.disembark_passengers())
        return disembarked_passengers

    def _board_passengers(self) -> list[Passenger]:
        boarded_passengers = []
        for platform in self.platforms:
            if not platform.can_move_passengers():
                continue
            if not platform.has_train():
                raise Exception("Attempt to board on platform with no train.")
            trains_next_stop = platform.get_next_station_id_for_train()
            boarded_this_platform = []
            for passenger in self.waiting_passengers:
                if platform.train_is_full():
                    break
                passenger_next_stop = passenger.get_next_station_id_on_route(self.id)
                if passenger_next_stop is None:
                    continue
                if trains_next_stop == passenger_next_stop:
                    boarded_passengers.append((passenger, platform.current_train_id()))
                    boarded_this_platform.append(passenger)
                    platform.embark_passenger(passenger)
                    self._filter_waiting_passengers(boarded_this_platform)

        self.passengers_boarded_trains += len(boarded_passengers)
        return boarded_passengers

    def _process_train_departures(self) -> None:
        for platform in self.platforms:
            if not platform.train_ready_for_departure():
                continue
            if not platform.has_train():
                raise Exception("Attempted to depart on platform with not train.")
            next_station_id = platform.get_next_station_id_for_train()
            if next_station_id not in self.outgoing_segments_lookup:
                raise Exception(
                    f"Outgoing train attempting to go station {next_station_id} from {self.name}:{self.id}, but no connection exists from station"
                )
            rail_segment = self.outgoing_segments_lookup[next_station_id]
            if rail_segment.can_take_another_train():
                train = platform.remove_train()
                rail_segment.accept_train(train)

    def _update_platform_states(self) -> None:
        for platform in self.platforms:
            if platform.platform_empty_state():
                continue
            platform.update_state()

    def _log_current_traffic(self) -> None:
        passengers_in_trains = 0
        for platform in self.platforms:
            platform.produce_state()
            passengers_in_trains += platform.current_train_passenger_count()

        passengers_waiting = len(self.waiting_passengers)
        total_passengers_on_premises = passengers_in_trains + passengers_waiting
        state = {
            "station_id": self.id,
            "clock_tick": self.clock.get_current_clock_tick(),
            "total_passengers_in_station": total_passengers_on_premises,
            "passengers_boarded_trains": self.passengers_boarded_trains,
            "passengers_entered_station": self.passengers_entered_station,
            "passengers_waiting": passengers_waiting,
        }
        self.system_event_bus.log_station_state(state)
        self.passengers_boarded_trains = 0
        self.passengers_entered_station = 0
