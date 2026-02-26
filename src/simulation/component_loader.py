import itertools
from collections import defaultdict
from collections import OrderedDict
import pandas as pd
from simulation.station import Station
from simulation.route import Route
from simulation.train import Train
from simulation.rail_segment import RailSegment
from simulation.passenger import Passenger
from simulation.travel_plan import TravelPlan
from simulation.world_clock import WorldClock
from simulation.platform_state import PlatformState
from simulation.data_reader import DataReader
from simulation.producer import Producer
from simulation.system_event_bus import SystemEventBus

"""
    Component Loader
    Aside from loading the state from the database.
    This class also does data validation, to avoid painful data corruption issues that could crash the simulation, or
    break the dashboard.
    There are 2 exceptions that can be raised in this file.
    They both originate from faulty configuration (system infrastructure seed files),
    or from runtime state files.
    No other types of exceptions are explicitly raised, since the code otherwise does not hit exceptions,
    due to the ComponentLoader not doing IO of any sort, as that is the job of the DataReader type.
    The script only requires validation related exceptions, which should fail (loudly) if triggered.
    Underneath these exceptions are IndexError, KeyError, and one ValueError, all from bad seed files.
    I elected to leave the exceptions generic, since the issue is ALWAYS in the seed files,
    which are human readable, the user just needs the error type as it pertains to the
    seed file issue, an IndexError for example doesnt help with inspecting of said files.
"""
class ConfigurationError(Exception):
    pass


class StateLoadingError(Exception):
    pass


class ComponentLoader:
    def __init__(self, data_reader: DataReader, producer: Producer):
        self.data_reader = data_reader
        self.stations = OrderedDict()
        self.trains_in_segments = defaultdict(list)
        self.trains_at_stations = defaultdict(list)
        self.incoming_segments = defaultdict(list)
        self.outgoing_segments = defaultdict(list)
        self.passengers = []
        self.passengers_in_trains = defaultdict(list)
        self.passengers_in_stations = defaultdict(list)

        self.train_routes_lookup: dict[int, Route] = {}
        self.passenger_routes_lookup: dict[int, Route] = {}

        self.world_clock = None
        self.system_event_bus = SystemEventBus(producer)

    def get_stations(self) -> dict[Station]:
        return self.stations

    def get_trains(self) -> list[Train]:
        trains_in_segments = self.trains_in_segments.values()
        flattened_trains_in_segments = list(
            itertools.chain.from_iterable(trains_in_segments)
        )
        trains_at_stations = self.trains_at_stations.values()
        flattened_trains_at_stations = list(
            itertools.chain.from_iterable(trains_at_stations)
        )
        return flattened_trains_in_segments + flattened_trains_at_stations

    def get_rail_segments(self) -> list[RailSegment]:
        return list(itertools.chain.from_iterable(self.incoming_segments.values()))

    def get_passengers(self) -> list[Passenger]:
        self.passengers.sort(key=lambda p: p.get_id())
        return self.passengers

    def get_world_clock(self) -> WorldClock:
        return self.world_clock

    def load_system_components(self) -> None:
        self._load_world_clock()
        self._load_passengers()
        self._load_trains()
        self._load_rail_segments()
        self._load_stations()
        self._data_integrity_checks()

    def _current_clock_tick(self) -> None:
        return self.world_clock.get_current_clock_tick()

    def _build_generic_routes_lookup(self, routes_df: pd.DataFrame) -> dict[int, Route]:
        routes = dict()
        for route_id in routes_df["route_id"].unique().tolist():
            specific_route_df = routes_df.loc[routes_df["route_id"] == route_id]
            specific_route_df = specific_route_df.drop("route_id", axis=1)
            specific_route_df = specific_route_df.sort_values(by="stop_sequence")
            stations = specific_route_df["station_id"].to_list()
            stops = specific_route_df["stop_sequence"].to_list()
            route = Route(route_id, stations, stops)
            routes[route_id] = route
        return routes

    def _load_world_clock(self) -> None:
        clock_df = self.data_reader.read_world_clock_state()
        if clock_df.empty:
            raise Exception("clock empty")
        latest_row = clock_df.sort_values(by="clock_tick", ascending=False).iloc[0]
        self.world_clock = WorldClock(
            clock_tick=int(latest_row["clock_tick"]),
            day_of_week=str(latest_row["day_of_week"]),
            year=int(latest_row["year"]),
            day_of_year=int(latest_row["day_of_year"]),
            hour_of_day=int(latest_row["hour_of_day"]),
            minute=int(latest_row["minute"]),
            system_event_bus=self.system_event_bus,
        )

    def _load_passengers(self) -> None:
        passengers_df = self.data_reader.read_passenger_itinerary()
        passenger_routes_df = self.data_reader.read_passenger_route_state()
        self.passenger_routes_lookup = self._build_generic_routes_lookup(
            passenger_routes_df
        )
        passenger_runtime_state_df = self._load_passenger_runtime_state()
        for passenger_id, group_df in passengers_df.groupby("id"):
            travel_plans = self._make_travel_plans_for_passenger(group_df)
            specific_passenger_runtime_state_df = passenger_runtime_state_df[
                passenger_runtime_state_df["passenger_id"] == passenger_id
            ]
            try:
                first_row = specific_passenger_runtime_state_df.iloc[0]
                self._make_passenger(first_row, travel_plans)
            except Exception:
                raise StateLoadingError("No matching passenger runtime state")

    def _make_travel_plans_for_passenger(
        self, group_df: pd.DataFrame
    ) -> list[TravelPlan]:
        travel_plans = []
        for row in group_df.to_dict("records"):
            try:
                travel_plan = TravelPlan(
                    self.passenger_routes_lookup[row["passenger_route_id"]],
                    int(row["start_arrival_hour"]),
                    int(row["arrival_minute"]),
                    str(row["travel_code"]),
                )
                travel_plans.append(travel_plan)
            except Exception as e:
                raise ConfigurationError(f"Failed to load travel plans {str(e)}")
        return travel_plans

    def _load_passenger_runtime_state(self) -> pd.DataFrame:
        passenger_state_df = self.data_reader.read_passenger_runtime_state()
        current_passenger_state_df = passenger_state_df[
            passenger_state_df["clock_tick"] <= self._current_clock_tick()
        ]
        return current_passenger_state_df.drop_duplicates(
            subset=["passenger_id"], keep="last"
        )

    def _make_passenger(self, row: pd.DataFrame, travel_plans: list[TravelPlan]):
        stops_so_far = row["stops_seen_so_far"]
        train_id = row["train_id"]
        station_id = row["station_id"]
        passenger = Passenger(
            id=int(row["passenger_id"]),
            travel_plans=travel_plans,
            world_clock=self.world_clock,
            system_event_bus=self.system_event_bus,
            stops_so_far=stops_so_far,
        )
        if pd.notna(train_id):
            self.passengers_in_trains[int(train_id)].append(passenger)
        elif pd.notna(station_id):
            self.passengers_in_stations[int(station_id)].append(passenger)
        if pd.notna(train_id) or pd.notna(station_id):
            passenger.resume_travelling()
            self._validate_stops_seen(passenger, stops_so_far)
        self.passengers.append(passenger)


    def _validate_stops_seen(self, passenger: Passenger, stops_so_far: list[int]):
        station_id = passenger.start_travelling()
        for recorded_station_id in stops_so_far:
            if station_id is None:
                raise ConfigurationError(
                    "Configuration for passenger stops is invalid, station id is None"
                )
            if recorded_station_id != station_id:
                raise StateLoadingError(
                    "Station Id does not match expected id for given stop number"
                )
            station_id = passenger.get_next_station_id_on_route(station_id)

    def _load_trains(self) -> None:
        train_routes_df = self.data_reader.read_train_route_state()
        self.train_routes_lookup = self._build_generic_routes_lookup(train_routes_df)
        train_state = self._load_train_state()
        train_configuration = self.data_reader.read_train_configuration()
        for line in train_configuration.to_dict("records"):
            train_id = int(line["train_id"])
            try:
                current_train_row = train_state[
                    train_state["train_id"] == train_id
                ].iloc[0]
            except Exception:
                raise StateLoadingError("Train is missing runtime state")
            stops_seen_so_far = [
                int(station_id) for station_id in current_train_row["stops_seen_so_far"]
            ]
            train = self._make_train(line, stops_seen_so_far)
            self._assign_train_to_location(train, current_train_row)

    def _make_train(self, line: dict[str, int], stops_seen_so_far: list[int]) -> Train:
        train_id = int(line["train_id"])
        route_id = int(line["route_id"])
        ordering = int(line["ordering"])
        capacity = int(line["capacity"])
        # Trains depend on routes to tell stations where they go next
        try:
            route = self.train_routes_lookup[route_id]
        except Exception:
            raise StateLoadingError("Missing route definition")
        self._validate_train_stops_seen_against_route(stops_seen_so_far, route)
        passengers = self.passengers_in_trains[train_id]
        try:
            return Train(
                id=train_id,
                route=route,
                ordering=ordering,
                capacity=capacity,
                clock=self.world_clock,
                passengers=passengers,
                stops_seen_so_far=stops_seen_so_far,
                system_event_bus=self.system_event_bus,
            )
        except Exception:
            raise StateLoadingError("Arguments to Train init are corrupted")

    def _validate_train_stops_seen_against_route(self, stops_seen_so_far: list[int], route: Route) -> None:
        station_ids = route.get_station_ids()
        if len(stops_seen_so_far) > len(station_ids):
            raise StateLoadingError(
                "stops seen by train contain more stations than the trains route"
            )
        for i in range(len(stops_seen_so_far)):
            if stops_seen_so_far[i] != station_ids[i]:
                raise StateLoadingError(
                    "Mismatch of stations seen against stations on trains route"
                )

    def _load_train_state(self) -> pd.DataFrame:
        train_state_df = self.data_reader.read_train_runtime_state()
        return train_state_df[
            train_state_df["clock_tick"] == self._current_clock_tick()
        ]

    def _assign_train_to_location(
        self, train: Train, train_state: pd.DataFrame
    ) -> None:
        station_id = train_state["station_id"]
        segment_id = train_state["segment_id"]
        if pd.notna(station_id):
            self.trains_at_stations[int(station_id)].append(train)
        elif pd.notna(segment_id):
            self.trains_in_segments[int(segment_id)].append(train)
        else:
            raise StateLoadingError(
                f"Train {train.get_id()} could not find location to be placed"
            )

    def _load_stations(self) -> None:
        station_config = self.data_reader.read_station_configuration()
        for line in station_config.to_dict("records"):
            station_id = int(line["station_id"])
            incoming_segments = self.incoming_segments[station_id]
            if len(incoming_segments) < 1:
                raise StateLoadingError(
                    "No matching incoming rail segments for station"
                )
            outgoing_segments = self.outgoing_segments[station_id]
            if len(outgoing_segments) < 1:
                raise StateLoadingError(
                    "No matching outgoing rail segments for station"
                )
            self.stations[station_id] = Station(
                station_id=station_id,
                station_name=line["station_name"],
                clock=self.world_clock,
                passengers=self.passengers_in_stations[station_id],
                trains=self.trains_at_stations[station_id],
                incoming_segments=incoming_segments,
                outgoing_segments=outgoing_segments,
                platform_states=self._make_platform_states_map(station_id),
                system_event_bus=self.system_event_bus,
            )

    def _load_station_runtime_state(self) -> pd.DataFrame:
        station_state_df = self.data_reader.read_station_runtime_state()
        station_state_df[["station_id", "route_id"]] = station_state_df[
            ["station_id", "route_id"]
        ].astype(int)
        current_station_state_df = station_state_df[
            station_state_df["clock_tick"] == self._current_clock_tick()
        ]
        return current_station_state_df

    def _make_platform_states_map(self, station_id: int) -> dict[str, str]:
        stations_state = self._load_station_runtime_state()
        station_state = stations_state[stations_state["station_id"] == station_id]
        if station_state.empty:
            raise StateLoadingError("Station missing runtime state")
        platform_state_code_map = station_state.set_index("route_id")[
            "platform_state"
        ].to_dict()
        return {
            plat_id: PlatformState.from_code(str(code))
            for plat_id, code in platform_state_code_map.items()
        }

    def _load_rail_segments(self) -> None:
        rail_segment_config = self.data_reader.read_rail_segments_configuration()
        for line in rail_segment_config.to_dict("records"):
            segment_id = int(line["segment_id"])
            from_station_id = int(line["from_station_id"])
            to_station_id = int(line["to_station_id"])
            distance_km = float(line["distance_km"])
            speed = float(line["speed"])
            ordered_train_position_maps_in_segment = (
                self._make_ordered_position_maps_for_segment(segment_id)
            )
            segment = RailSegment(
                segment_id,
                from_station_id=from_station_id,
                to_station_id=to_station_id,
                distance_km=distance_km,
                speed=speed,
                ordered_train_position_maps_in_segment=ordered_train_position_maps_in_segment,
                system_event_bus=self.system_event_bus,
                world_clock=self.world_clock,
            )
            """
              It should be noted that if all the trains are at the end, or beginning
              this could throw the original order off if two or more trains have the same ordering
              for their route, and the same distance (2+ trains, different routes).
              However, trains from different routes are allowed to show up at various times,
              since multiple routes use the same rail segments, so this isn't really an issue.
            """
            self.incoming_segments[to_station_id].append(segment)
            self.outgoing_segments[from_station_id].append(segment)

    def _make_ordered_position_maps_for_segment(self, segment_id) -> list[dict]:
        ordered_train_state_for_segment = self._make_ordered_train_state_for_segment(
            segment_id
        )
        return self._populate_position_map_entries(
            segment_id, ordered_train_state_for_segment
        )

    def _populate_position_map_entries(
        self,
        segment_id: int,
        ordered_train_state_for_segment: list[dict],
    ) -> list[dict]:
        ordered_trains_with_position = []
        trains_in_segment_lookup = {
            t.get_id(): t for t in self.trains_in_segments[segment_id]
        }
        if len(trains_in_segment_lookup) != len(ordered_train_state_for_segment):
            raise StateLoadingError(
                f"Mismatch between rail segment state {ordered_train_state_for_segment}\n\nand known train locations: {trains_in_segment_lookup}"
            )
        for train_location in ordered_train_state_for_segment:
            train_id = train_location["id"]
            train_position_km = train_location["position_km"]
            train_in_segment = trains_in_segment_lookup.get(train_id, None)
            if train_in_segment is None:
                raise StateLoadingError(
                    f"Train {train_id} listed in rail segment state but not found in segment"
                )
            position_map = {"train": train_in_segment, "position_km": train_position_km}
            ordered_trains_with_position.append(position_map)
        return ordered_trains_with_position

    def _make_ordered_train_state_for_segment(self, segment_id: int) -> list[dict]:
        rail_segment_state = self._load_rail_segment_runtime_state()
        try:
            state_for_segment = rail_segment_state[
                rail_segment_state["segment_id"] == segment_id
            ]
        except Exception as e:
            raise StateLoadingError(f"Rail segment missing runtime state: {str(e)}")

        if state_for_segment.empty:
            return []

        latest_state = state_for_segment.sort_values(by="clock_tick").iloc[-1]
        return latest_state["trains_present"]

    def _load_rail_segment_runtime_state(self) -> pd.DataFrame:
        rail_segment_state_df = self.data_reader.read_rail_segment_runtime_state()
        current_rail_segment_state_df = rail_segment_state_df[
            rail_segment_state_df["clock_tick"] == self._current_clock_tick()
        ]
        return current_rail_segment_state_df

    def _data_integrity_checks(self) -> None:
        self._check_for_orphaned_trains()
        self._check_stations_connections()
        self._check_trains_on_valid_segments()
        self._check_passenger_location_consistency()
        self._check_stations_have_platforms_for_routes()
        self._check_platforms_have_valid_routes()
        self._check_route_physical_connectivity()

    def _check_for_orphaned_trains(self) -> None:
        loaded_train_ids = set(t.id for t in self.get_trains())
        located_train_ids = set()
        for station_id, trains in self.trains_at_stations.items():
            for train in trains:
                located_train_ids.add(train.id)
        for trains in self.trains_in_segments.values():
            for train in trains:
                located_train_ids.add(train.id)
        orphans = loaded_train_ids - located_train_ids
        if orphans:
            raise StateLoadingError(
                f"Trains {orphans} loaded but not placed in any station or segment."
            )
        defined_station_ids = set(self.stations.keys())
        for station_id in self.trains_at_stations.keys():
            if station_id not in defined_station_ids:
                raise ConfigurationError(
                    f"Trains located at undefined Station {station_id}"
                )

    def _check_stations_connections(self) -> None:
        segment_connections = set()
        for segment in self.get_rail_segments():
            segment_connections.add((segment.from_station_id, segment.to_station_id))

        for start, end in segment_connections:
            if (end, start) not in segment_connections:
                raise ConfigurationError(
                    f"Invalid Station Connectivity: Segment exists from {start}->{end}, "
                    f"but no return segment {end}->{start} is defined."
                )

    def _check_trains_on_valid_segments(self) -> None:
        segment_map = {s.id: s for s in self.get_rail_segments()}
        for segment_id, trains in self.trains_in_segments.items():
            segment = segment_map.get(segment_id)
            if not segment:
                raise ConfigurationError(
                    f"Trains loaded into undefined segment {segment_id}"
                )
            for train in trains:
                route_stations = train.route.get_station_ids()
                is_valid_transition = False
                for i in range(len(route_stations) - 1):
                    if (
                        route_stations[i] == segment.from_station_id
                        and route_stations[i + 1] == segment.to_station_id
                    ):
                        is_valid_transition = True
                        break
                if not is_valid_transition:
                    if (
                        route_stations[-1] == segment.from_station_id
                        and route_stations[0] == segment.to_station_id
                    ):
                        is_valid_transition = True

                if not is_valid_transition:
                    raise ConfigurationError(
                        f"Train {train.id} is in segment {segment.id} ({segment.from_station_id}->{segment.to_station_id}), "
                        f"but this transition is not part of its Route {train.route.id}: {route_stations}"
                    )

    def _check_passenger_location_consistency(self) -> None:
        for passenger in self.passengers:
            if self._found_passenger_in_station(passenger):
                continue
            if self._found_passenger_on_train(passenger):
                continue
            raise StateLoadingError(
                f"Passenger {passenger.id} is marked as 'travelling' but was not found in any Station or Train."
            )

    def _found_passenger_in_station(self, passenger: Passenger) -> bool:
        if not passenger.is_in_system():
            return True
        for station_id, passenger_list in self.passengers_in_stations.items():
            if passenger in passenger_list:
                if station_id not in passenger.current_route.get_station_ids():
                    raise ConfigurationError(
                        f"Passenger {passenger.id} is at Station {station_id}, which is not on their current Route {passenger.current_route.id}"
                    )
                return True
        return False

    def _found_passenger_on_train(self, passenger: Passenger) -> bool:
        for train_id, passenger_list in self.passengers_in_trains.items():
            if passenger in passenger_list:
                train = next((t for t in self.get_trains() if t.id == train_id), None)
                if not train:
                    raise StateLoadingError(
                        f"Passenger {passenger.id} loaded into non-existent Train {train_id}"
                    )
                return True
        return False

    def _check_stations_have_platforms_for_routes(self) -> None:
        for route in self.train_routes_lookup.values():
            for station_id in route.get_station_ids():
                station = self.stations.get(station_id)
                if not station:
                    raise ConfigurationError(
                        f"Route {route.id} includes undefined Station {station_id}"
                    )
                has_platform = any(p.route_id == route.id for p in station.platforms)
                if not has_platform:
                    raise ConfigurationError(
                        f"Station {station_id} is on Route {route.id}, but has no platform configured for it."
                    )

    def _check_platforms_have_valid_routes(self) -> None:
        valid_route_ids = set(self.train_routes_lookup.keys())
        for station in self.stations.values():
            for platform in station.platforms:
                if platform.route_id not in valid_route_ids:
                    raise ConfigurationError(
                        f"Station {station.id} has a platform for Route {platform.route_id}, which is not defined in train routes."
                    )

    def _check_route_physical_connectivity(self) -> None:
        valid_segments = set()
        for s in self.get_rail_segments():
            valid_segments.add((s.from_station_id, s.to_station_id))
        all_routes = list(self.train_routes_lookup.values()) + list(
            self.passenger_routes_lookup.values()
        )
        for route in all_routes:
            station_ids = route.get_station_ids()
            if len(station_ids) < 2:
                raise ConfigurationError(
                    f"Route {route.id} must have at least 2 stations to be valid."
                )
            for i in range(len(station_ids) - 1):
                from_id = station_ids[i]
                to_id = station_ids[i + 1]
                if (from_id, to_id) not in valid_segments:
                    raise ConfigurationError(
                        f"Route {route.id} requires travel from Station {from_id} to {to_id}, "
                        f"but no connecting rail segment exists."
                    )
