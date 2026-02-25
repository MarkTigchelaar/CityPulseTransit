
import os
import pandas as pd
from sqlalchemy import create_engine
from streamlit import cache_resource

DB_SCHEMA = os.getenv("DB_SCHEMA", "public_transit")
DB_CONNECTION = "postgresql://thomas:mind_the_gap@localhost:5432/subway_system"


class DataService:
    def __init__(self):
        self.engine = self._get_engine()
        self.clock_df = None
        self.kpi_df = None
        self.station_crowding_df = None
        self.fleet_df = None
        self.topology_df = None
        self.map_df = None
        self.wait_time_df = None
        self.headway_df = None
        self.track_df = None

    @cache_resource
    def _get_engine(_self):
        return create_engine(DB_CONNECTION)

    def fetch_world_clock(self) -> pd.DataFrame:
        if self.clock_df is not None:
            return self.clock_df
        query = f"SELECT clock_tick, year, month_name, day_name, day_of_month, hour_of_day, minute FROM {DB_SCHEMA}.mart_world_clock"
        self.clock_df = pd.read_sql(query, self.engine)
        return self.clock_df

    def fetch_kpis(self):
        if self.kpi_df is not None:
            return self.kpi_df
        query = f"SELECT * FROM {DB_SCHEMA}.mart_live_system_kpis"
        self.kpi_df = pd.read_sql(query, self.engine)
        return self.kpi_df

    def fetch_station_crowding_status(self):
        if self.station_crowding_df is not None:
            return self.station_crowding_df
        query = f"""
            SELECT 
                station_name, 
                total_passengers_in_station,
                passengers_waiting
            FROM {DB_SCHEMA}.mart_live_station_crowding
            ORDER BY total_passengers_in_station DESC
        """
        self.station_crowding_df = pd.read_sql(query, self.engine)
        return self.station_crowding_df

    def fetch_fleet_status(self):
        if self.fleet_df is not None:
            return self.fleet_df
        query = f"""
            SELECT 
                train_id, 
                route_id, 
                status, 
                passenger_count, 
                utilization_pct,
                distance_from_start_km
            FROM {DB_SCHEMA}.mart_live_train_positions
            ORDER BY route_id, train_id
        """
        self.fleet_df = pd.read_sql(query, self.engine)
        return self.fleet_df


    def fetch_map_topology(self):
        if self.topology_df is not None:
            return self.topology_df
        query = f"""
            select
                *
            from 
                {DB_SCHEMA}.mart_route_topology
            """
        self.topology_df = pd.read_sql(query, self.engine)
        return self.topology_df

    def fetch_headway_status(self):
        if self.headway_df is not None:
            return self.headway_df
        query = f"""
            select
                train_id,
                route_id,
                train_ahead_id,
                gap_km,
                spacing_health
            from
                {DB_SCHEMA}.mart_live_headways
            """
        self.headway_df = pd.read_sql(query, self.engine)
        return self.headway_df


    def fetch_static_map(self):
        if self.map_df is not None:
            return self.map_df
        query = f"""
            select
                route_id,
                station_name,
                next_station_name
            from
                {DB_SCHEMA}.mart_system_topology_edges
            """
        self.map_df = pd.read_sql(query, self.engine)
        return self.map_df

    def fetch_wait_times(self):
        if self.wait_time_df is not None:
            return self.wait_time_df
        query = f"""
            select
                metric,
                wait_time
            from
                {DB_SCHEMA}.mart_live_wait_times
            """
        self.wait_time_df = pd.read_sql(query, self.engine)
        return self.wait_time_df


    def fetch_track_df(self):
        if self.track_df is not None:
            return self.track_df
        topology_df = self.fetch_map_topology()
        self.track_df = (
            topology_df.groupby("route_id")["distance_from_start_km"]
            .agg(["min", "max"])
            .reset_index()
        )
        self.track_df.columns = ["route_id", "start_km", "end_km"]
        return self.track_df
