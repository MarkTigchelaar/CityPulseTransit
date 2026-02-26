import pandas as pd
from sqlalchemy import create_engine
from simulation.data_reader import DataReader
from config import DB_CONNECTION, DB_SCHEMA


class TableDataReader(DataReader):
    def __init__(self):
        self.engine = create_engine(DB_CONNECTION)
        self._latest_tick = None
        print(f"connecting to schema: {DB_SCHEMA}")

    def _read_table(self, table_name: str) -> pd.DataFrame:
        """Reads static configuration tables entirely into memory."""
        return pd.read_sql_table(table_name, self.engine, schema=DB_SCHEMA)

    def _ensure_clock_loaded(self):
        """Explodes if a runtime component tries to load before the world clock."""
        if self._latest_tick is None:
            raise RuntimeError("CRITICAL: World clock must be loaded first to determine the current tick!")

    # --- CONFIGURATION ---
    def read_train_route_state(self) -> pd.DataFrame:
        return self._read_table("stg_routes")

    def read_train_configuration(self) -> pd.DataFrame:
        return self._read_table("stg_trains")

    def read_rail_segments_configuration(self) -> pd.DataFrame:
        return self._read_table("stg_rail_segments")

    def read_station_configuration(self) -> pd.DataFrame:
        return self._read_table("stg_stations")

    def read_passenger_itinerary(self) -> pd.DataFrame:
        return self._read_table("stg_passenger_itinerary")

    def read_passenger_route_state(self) -> pd.DataFrame:
        return self._read_table("stg_passenger_routes")

    # --- RUNTIME ---
    def read_world_clock_state(self) -> pd.DataFrame:
        df = self._read_table("stg_world_clock_state")
        if not df.empty:
            self._latest_tick = int(df["clock_tick"].max())
        else:
            self._latest_tick = 0
        return df

    def read_train_runtime_state(self) -> pd.DataFrame:
        self._ensure_clock_loaded()
        query = f"SELECT * FROM {DB_SCHEMA}.stg_train_state WHERE clock_tick = {self._latest_tick}"
        return pd.read_sql_query(query, self.engine)

    def read_station_runtime_state(self) -> pd.DataFrame:
        self._ensure_clock_loaded()
        query = f"SELECT * FROM {DB_SCHEMA}.stg_platform_state WHERE clock_tick = {self._latest_tick}"
        return pd.read_sql_query(query, self.engine)

    def read_rail_segment_runtime_state(self) -> pd.DataFrame:
        self._ensure_clock_loaded()
        query = f"SELECT * FROM {DB_SCHEMA}.stg_rail_segment_state WHERE clock_tick = {self._latest_tick}"
        return pd.read_sql_query(query, self.engine)

    def read_passenger_runtime_state(self) -> pd.DataFrame:
        self._ensure_clock_loaded()
        query = f"""
            SELECT DISTINCT ON (passenger_id) *
            FROM {DB_SCHEMA}.stg_passenger_state
            WHERE clock_tick <= {self._latest_tick}
            ORDER BY passenger_id, clock_tick DESC
        """
        return pd.read_sql_query(query, self.engine)
