import pandas as pd
from sqlalchemy import create_engine
from data_reader import DataReader

DB_CONNECTION = "postgresql://thomas:mind_the_gap@localhost:5432/subway_system"
SCHEMA = "public_transit"

class TableDataReader(DataReader):
    def __init__(self):
        self.engine = create_engine(DB_CONNECTION)
        print(f"connecting to schema: {SCHEMA}")

    def _read_table(self, table_name: str) -> pd.DataFrame:
        return pd.read_sql_table(table_name, self.engine, schema=SCHEMA)


    # read configuration of transit system
    def read_train_route_state(self) -> pd.DataFrame:
        return self._read_table("routes")

    def read_train_configuration(self) -> pd.DataFrame:
        return self._read_table("trains")

    def read_rail_segments_configuration(self) -> pd.DataFrame:
        return self._read_table("rail_segments")

    def read_station_configuration(self) -> pd.DataFrame:
        return self._read_table("stations")

    def read_passenger_itinerary(self) -> pd.DataFrame:
        return self._read_table("passenger_itinerary")

    def read_passenger_route_state(self) -> pd.DataFrame:
        return self._read_table("passenger_routes")


    # read runtime state
    def read_world_clock_state(self) -> pd.DataFrame:
        return self._read_table("runtime_world_clock_state")

    def read_train_runtime_state(self) -> pd.DataFrame:
        return self._read_table("runtime_train_state")

    def read_station_runtime_state(self) -> pd.DataFrame:
        return self._read_table("runtime_station_state")

    def read_user_adjustable_variables(self) -> pd.DataFrame:
        return self._read_table("runtime_user_adjustable_variables_state")

    def read_passenger_runtime_state(self) -> pd.DataFrame:
        return self._read_table("runtime_passenger_state")

    def read_rail_segment_runtime_state(self) -> pd.DataFrame:
        return self._read_table("runtime_rail_segment_state")
