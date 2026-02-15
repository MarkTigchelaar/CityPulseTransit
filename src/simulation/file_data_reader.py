import pandas as pd
from simulation.data_reader import DataReader


TEST_DATA_PATH = "test_seed_data/"

# This is for debugging, and manual output inspection.
# Not really needed, only at the beginning, but I left it here anyway.
class FileDataReader(DataReader):
    def __init__(self):
        # infrastructure (static) state
        self.STATIONS = TEST_DATA_PATH + "stations.csv"
        self.ROUTES = TEST_DATA_PATH + "routes.csv"
        self.TRAINS = TEST_DATA_PATH + "trains.csv"
        self.RAIL_SEGMENTS = TEST_DATA_PATH + "rail_segments.csv"
        self.PASSENGER_ITINERARY = TEST_DATA_PATH + "passenger_itinerary.csv"
        self.PASSENGER_ROUTES = TEST_DATA_PATH + "passenger_routes.csv"
        # runtime state:
        self.WORLD_CLOCK_STATE = TEST_DATA_PATH + "world_clock_state.csv"
        self.ADJUSTABLE_VARIABLES = TEST_DATA_PATH + "user_adjustable_variables.csv"
        self.TRAIN_STATE = TEST_DATA_PATH + "train_state.csv"
        self.STATION_STATE = TEST_DATA_PATH + "station_state.csv"
        self.PASSENGER_STATE = TEST_DATA_PATH + "passenger_state.csv"
        self.RAIL_SEGMENT_STATE = TEST_DATA_PATH + "rail_segment_state.csv"

    # Let these fail loudly
    def _read_csv_as_dataframe(self, filename: str) -> pd.DataFrame:
        return pd.read_csv(filename, index_col=False)

    def read_world_clock_state(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.WORLD_CLOCK_STATE)

    def read_user_adjustable_variables(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.ADJUSTABLE_VARIABLES)

    def read_passenger_itinerary(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.PASSENGER_ITINERARY)

    def read_passenger_runtime_state(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.PASSENGER_STATE)

    def read_passenger_route_state(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.PASSENGER_ROUTES)

    def read_train_route_state(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.ROUTES)

    def read_train_runtime_state(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.TRAIN_STATE)

    def read_train_configuration(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.TRAINS)

    def read_rail_segments_configuration(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.RAIL_SEGMENTS)

    def read_station_configuration(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.STATIONS)

    def read_station_runtime_state(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.STATION_STATE)

    def read_rail_segment_runtime_state(self) -> pd.DataFrame:
        return self._read_csv_as_dataframe(self.RAIL_SEGMENT_STATE)
