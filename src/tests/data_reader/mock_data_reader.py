import pandas as pd
from typing import List, Dict, Any
from src.simulation.data_reader.data_reader import DataReader


class UnittestDataReader(DataReader):
    """
    In-memory data reader for testing.
    Accepts lists of dicts and converts them to DataFrames/Iterators
    expected by ComponentLoader.
    Ensures DataFrames always have the correct columns to prevent KeyErrors on empty datasets.
    """

    def __init__(
        self,
        world_clock_config: Dict[str, Any] = None,
        station_config: List[Dict[str, Any]] = None,
        station_runtime_state: List[Dict[str, Any]] = None,
        train_config: List[Dict[str, Any]] = None,
        train_runtime_state: List[Dict[str, Any]] = None,
        rail_segment_config: List[Dict[str, Any]] = None,
        route_config: List[Dict[str, Any]] = None,
        passenger_itinerary: List[Dict[str, Any]] = None,
        passenger_routes: List[Dict[str, Any]] = None,
        passenger_runtime_state: List[Dict[str, Any]] = None,
        rail_segment_runtime_state: List[Dict[str, Any]] = None,
    ):
        self.world_clock_data = [world_clock_config] if world_clock_config else []
        self.station_config = station_config or []
        self.station_runtime_state = station_runtime_state or []
        self.train_config = train_config or []
        self.train_runtime_state = train_runtime_state or []
        self.rail_segment_config = rail_segment_config or []
        self.route_config = route_config or []
        self.passenger_itinerary = passenger_itinerary or []
        self.passenger_routes = passenger_routes or []
        self.passenger_runtime_state = passenger_runtime_state or []
        self.rail_segment_state = rail_segment_runtime_state or []

    def _create_dataframe(self, data: List[Dict], columns: List[str]) -> pd.DataFrame:
        if not data:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame(data, columns=columns)

    def read_world_clock_state(self) -> pd.DataFrame:
        columns = ["clock_tick", "year", "day_of_year", "day_of_week", "hour_of_day", "minute"]
        return self._create_dataframe(self.world_clock_data, columns=columns)
    
    def read_train_route_state(self) -> pd.DataFrame:
        columns = ["route_id", "station_id", "stop_sequence"]
        return self._create_dataframe(self.route_config, columns)

    def read_train_runtime_state(self) -> pd.DataFrame:
        columns = ["clock_tick", "train_id", "station_id", "segment_id", "position_km", "stops_seen_so_far"]
        return self._create_dataframe(self.train_runtime_state, columns=columns)


    def read_station_runtime_state(self) -> pd.DataFrame:
        columns = ["clock_tick", "station_id", "route_id", "platform_state"]
        return self._create_dataframe(self.station_runtime_state, columns)

    def read_train_configuration(self) -> pd.DataFrame:
        columns = ["train_id", "route_id", "ordering", "capacity"]
        return self._create_dataframe(self.train_config, columns)

    def read_rail_segments_configuration(self) -> pd.DataFrame:
        columns = ["segment_id", "from_station_id", "to_station_id", "distance_km", "speed"]
        return self._create_dataframe(self.rail_segment_config, columns)

    def read_station_configuration(self) -> pd.DataFrame:
        columns = ["station_id", "station_name"]
        return self._create_dataframe(self.station_config, columns)

    def read_passenger_itinerary(self) -> pd.DataFrame:
        columns = [
            "id",
            "passenger_route_id",
            "start_arrival_hour",
            "arrival_minute",
            "travel_code",
        ]
        return self._create_dataframe(self.passenger_itinerary, columns)

    def read_passenger_route_state(self) -> pd.DataFrame:
        columns = ["route_id", "station_id", "stop_sequence"]
        return self._create_dataframe(self.passenger_routes, columns)

    def read_passenger_runtime_state(self) -> pd.DataFrame:
        # Swap it here too
        columns = ["clock_tick", "passenger_id", "train_id", "station_id", "stops_seen_so_far"]
        return self._create_dataframe(self.passenger_runtime_state, columns=columns)

    def read_rail_segment_runtime_state(self) -> pd.DataFrame:
        columns = ["segment_id", "clock_tick", "train_queuing_order", "train_id", "trains_present"]
        return self._create_dataframe(self.rail_segment_state, columns)
