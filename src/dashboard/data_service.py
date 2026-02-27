import pandas as pd
from sqlalchemy import create_engine
from streamlit import cache_resource
from src.config import DB_CONNECTION, DB_SCHEMA

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
        query = f"""
            select
                clock_tick,
                year,
                month_name,
                day_name,
                day_of_month,
                hour_of_day,
                minute
            from
                {DB_SCHEMA}.mart_world_clock
            """
        self.clock_df = pd.read_sql(query, self.engine)
        return self.clock_df

    def fetch_kpis(self):
        if self.kpi_df is not None:
            return self.kpi_df
        query = f"""
            select
                total_passengers_in_system,
                total_passengers_riding,
                total_passengers_waiting,
                avg_network_utilization_pct,
                active_trains
            from
                {DB_SCHEMA}.mart_live_system_kpis
            """
        self.kpi_df = pd.read_sql(query, self.engine)
        return self.kpi_df

    def fetch_station_crowding_status(self):
        if self.station_crowding_df is not None:
            return self.station_crowding_df
        query = f"""
            select 
                station_name, 
                total_passengers_in_station,
                passengers_waiting
            from
                {DB_SCHEMA}.mart_live_station_crowding
            order by
                total_passengers_in_station
            desc
        """
        self.station_crowding_df = pd.read_sql(query, self.engine)
        return self.station_crowding_df

    def fetch_fleet_status(self):
        if self.fleet_df is not None:
            return self.fleet_df
        query = f"""
            select 
                train_id, 
                route_id, 
                status, 
                passenger_count, 
                utilization_pct,
                distance_from_start_km
            from
                {DB_SCHEMA}.mart_live_train_positions
            order by
                route_id, train_id
        """
        self.fleet_df = pd.read_sql(query, self.engine)
        return self.fleet_df

    def fetch_map_topology(self):
        if self.topology_df is not None:
            return self.topology_df
        query = f"""
            select
                route_id,
                stop_sequence,
                station_name,
                segment_km,
                distance_from_start_km
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
                map_x,
                map_y,
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
