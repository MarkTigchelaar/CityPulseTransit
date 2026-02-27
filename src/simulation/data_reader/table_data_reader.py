import pandas as pd
from sqlalchemy import create_engine
from src.simulation.data_reader.data_reader import DataReader
from src.config import DB_CONNECTION, DB_SCHEMA


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
        clock_state_df = self._read_table("stg_world_clock_state")
        if not clock_state_df.empty:
            self._latest_tick = int(clock_state_df["clock_tick"].max())
        else:
            self._latest_tick = 0
        return clock_state_df

    def read_train_runtime_state(self) -> pd.DataFrame:
        self._ensure_clock_loaded()
        query = f"""
            select
                clock_tick,
                train_id,
                segment_id,
                station_id,
                stops_seen_so_far,
                passenger_count
            from
                {DB_SCHEMA}.stg_train_state
            where
                clock_tick = {self._latest_tick}
            """
        return pd.read_sql_query(query, self.engine)

    def read_station_runtime_state(self) -> pd.DataFrame:
        self._ensure_clock_loaded()
        query = f"""
            select
                station_id,
                clock_tick,
                route_id,
                platform_state
            from
                {DB_SCHEMA}.stg_platform_state
            where
                clock_tick = {self._latest_tick}
            """
        return pd.read_sql_query(query, self.engine)

    def read_rail_segment_runtime_state(self) -> pd.DataFrame:
        self._ensure_clock_loaded()
        query = f"""
            select
                segment_id,
                clock_tick,
                trains_present
            from
                {DB_SCHEMA}.stg_rail_segment_state
            where
                clock_tick = {self._latest_tick}
            """
        return pd.read_sql_query(query, self.engine)

    def read_passenger_runtime_state(self) -> pd.DataFrame:
        self._ensure_clock_loaded()
        query = f"""
            select distinct on (passenger_id)
                clock_tick,
                passenger_id,
                train_id,
                station_id,
                stops_seen_so_far
            from
                {DB_SCHEMA}.stg_passenger_state
            where
                clock_tick <= {self._latest_tick}
            order by
                passenger_id,
                clock_tick
            desc
            """
        return pd.read_sql_query(query, self.engine)
