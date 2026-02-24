import os
import colorsys
import pandas as pd
import streamlit as st
import altair as alt
from streamlit_autorefresh import st_autorefresh
from sqlalchemy import create_engine

# --- Configuration ---
DB_SCHEMA = os.getenv("DB_SCHEMA", "public_transit")
DB_CONNECTION = "postgresql://thomas:mind_the_gap@localhost:5432/subway_system"
REFRESH_SECONDS = 2

# Auto-refresh the page every 1 second
st_autorefresh(interval=1000, limit=None, key="city_pulse_refresher")

# st.set_page_config(
#     page_title="Dashboard",
#     page_icon="🚄",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )


class TransitDashboard:
    def __init__(self):
        self.title = "City Pulse Transit Dashboard"
        self.engine = self._get_engine()
        self.clock_df = pd.DataFrame()

    @st.cache_resource
    def _get_engine(_self):
        return create_engine(DB_CONNECTION)

    def fetch_world_clock(self):
        query = f"SELECT clock_tick, year, month_name, day_name, day_of_month, hour_of_day, minute FROM {DB_SCHEMA}.mart_world_clock"
        #try:
        self.clock_df = pd.read_sql(query, self.engine)
        # except:
        #     self.clock_df = pd.DataFrame()

    def render_header(self):
        st.title(self.title)
        if not self.clock_df.empty:
            # Grab the row once
            row = self.clock_df.iloc[0]
            
            year = int(row["year"])
            hour = int(row["hour_of_day"])
            minute = int(row["minute"])
            day_name = row["day_name"]
            month_name = row["month_name"]
            day_of_month = int(row["day_of_month"])
            
            # Format: "Monday, January 15, 2026 | 08:30"
            st.markdown(f"### 🕒 {day_name}, {month_name} {day_of_month}, {year} | {hour:02d}:{minute:02d}")
        else:
            st.markdown("### 🕒 System Offline")

    def fetch_kpis(self):
        query = f"SELECT * FROM {DB_SCHEMA}.mart_live_system_kpis"
        self.kpi_df = pd.read_sql(query, self.engine)

    def render_kpis(self):
        if self.kpi_df.empty:
            return

        # Grab the single row of pre-calculated data
        kpis = self.kpi_df.iloc[0]

        # Use columns to lay them out nicely
        col1, col2, col3, col4 = st.columns(4)

        # Keep labels short! Put the cut-off descriptions in the `help` tooltip.
        col1.metric(
            label="Total in System", 
            value=f"{kpis['total_passengers_in_system']:,}",
            help="The total number of passengers currently tracked anywhere in the network (riding + waiting)."
        )
        
        col2.metric(
            label="Passengers Riding", 
            value=f"{kpis['total_passengers_riding']:,}",
            help="Passengers currently onboard an active train."
        )
        
        col3.metric(
            label="Passengers Waiting", 
            value=f"{kpis['total_passengers_waiting']:,}",
            help="Passengers standing on platforms waiting for a train to arrive."
        )
        
        col4.metric(
            label="Network Utilization", 
            value=f"{kpis['avg_network_utilization_pct']}%",
            help="The average capacity utilization across all active trains."
        )

        st.markdown("---")

    def render_content_area(self):
        tab_map, tab_matrix, tab_network, tab_crowd,  tab_bunching, tab_service_quality = st.tabs(
            ["🗺️ Live Map", "🏗️ Fleet Matrix", "System Map", "🌡️ Crowd Meter", "Train bunching", "Service Quality"]
        )
        with tab_map:
            self.render_linear_map()
        with tab_matrix:
            self.render_fleet_matrix()
        with tab_network:
            self.render_network_map()
        with tab_crowd:
            self.render_crowd_meter()
        with tab_bunching:
            self.render_headway_monitor()
        with tab_service_quality:
            dashboard.render_wait_times()
        

    def fetch_station_crowding_status(self):
        query = f"""
            SELECT 
                station_name, 
                total_passengers_in_station,
                passengers_waiting
            FROM {DB_SCHEMA}.mart_live_station_crowding
            ORDER BY total_passengers_in_station DESC
        """
        self.station_crowding_df = pd.read_sql(query, self.engine)
    
    def fetch_fleet_status(self):
        # Reusing the map mart! The Single Source of Truth.
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

    def fetch_static_map(self):
        query = f"SELECT route_id, station_name, next_station_name FROM {DB_SCHEMA}.mart_system_topology_edges"
        self.map_df = pd.read_sql(query, self.engine)

    def fetch_headways(self):
        # One simple query, zero Pandas math
        query = f"SELECT train_id, route_id, train_ahead_id, gap_km, spacing_health FROM {DB_SCHEMA}.mart_live_headways"
        self.headway_df = pd.read_sql(query, self.engine)

    def fetch_wait_times(self):
        query = f"SELECT metric, wait_time FROM {DB_SCHEMA}.mart_live_wait_times"
        self.wait_time_df = pd.read_sql(query, self.engine)

    
    def render_linear_map(self):
        st.subheader("📍 Live Network Velocity")

        topology_df = pd.read_sql(
            f"select * from {DB_SCHEMA}.mart_route_topology", self.engine
        )

        if topology_df.empty:
            st.warning("No route topology data found.")
            return

        track_df = (
            topology_df.groupby("route_id")["distance_from_start_km"]
            .agg(["min", "max"])
            .reset_index()
        )
        track_df.columns = ["route_id", "start_km", "end_km"]

        system_max_km = track_df["end_km"].max()
        route_domain = sorted(topology_df["route_id"].unique().tolist())

        x_scale = alt.Scale(domain=[0, system_max_km], nice=False)
        y_scale = alt.Scale(domain=route_domain)


        track_layer = (
            alt.Chart(track_df)
            .mark_rule(color="#444", strokeWidth=3)
            .encode(
                x=alt.X("start_km:Q", scale=x_scale, title="Distance (km)"),
                x2="end_km:Q",
                y=alt.Y("route_id:O", scale=y_scale, title="Route"),
            )
        )


        station_layer = (
            alt.Chart(topology_df)
            .mark_circle(size=100, color="white", opacity=1.0)
            .encode(
                x=alt.X("distance_from_start_km:Q", scale=x_scale),
                y=alt.Y("route_id:O", scale=y_scale),
                tooltip=["station_name", "distance_from_start_km"],
            )
        )

        if not self.fleet_df.empty:
            plot_df = self.fleet_df.copy()
            if "distance_from_start_km" in plot_df.columns:
                plot_df["distance_from_start_km"] = plot_df[
                    "distance_from_start_km"
                ].astype(float)

            plot_df["distance_from_start_km"] = plot_df["distance_from_start_km"].clip(
                upper=system_max_km
            )

            trains = (
                alt.Chart(plot_df)
                .mark_point(shape="triangle-right", size=200, filled=True)
                .encode(
                    x=alt.X("distance_from_start_km:Q", scale=x_scale),
                    y=alt.Y("route_id:O", scale=y_scale),
                    color=alt.Color(
                        "utilization_pct",
                        scale=alt.Scale(scheme="redyellowgreen", domain=[100, 0]),
                        title="Load %",
                    ),
                    tooltip=["train_id", "passenger_count", "status"],
                )
            )
            combined_chart = track_layer + station_layer + trains
        else:
            combined_chart = track_layer + station_layer
        st.altair_chart(
            combined_chart.properties(height=300),
            use_container_width=True,
            theme=None
        )


    def render_crowd_meter(self):
        st.subheader("🌡️ Station Crowd Density")
        if self.station_crowding_df.empty:
            st.info("Awaiting passenger data...")
            return

        current_max = self.station_crowding_df['total_passengers_in_station'].max()
        y_max = current_max if pd.notna(current_max) and current_max > 0 else 10

        chart = alt.Chart(self.station_crowding_df).mark_bar().encode(
            x=alt.X('station_name:N', sort='-y', title="Station"),
            
            y=alt.Y('total_passengers_in_station:Q', 
                    title="Passengers Waiting", 
                    scale=alt.Scale(domain=[0, y_max])), 
                    
            color=alt.Color('total_passengers_in_station:Q', legend=None)
        ).properties(
            height=300
        )
        
        st.altair_chart(chart, use_container_width=True, theme=None)

    def render_fleet_matrix(self):
        st.subheader("🏗️ Fleet Status Matrix")
        if self.fleet_df.empty:
            st.info("No trains currently active in the network.")
            return
        
        st.divider()
        st.dataframe(
            self.fleet_df,
            column_config={
                "train_id": st.column_config.TextColumn("Train ID"),
                "route_id": st.column_config.NumberColumn("Route", format="%d"),
                "status": st.column_config.TextColumn("Current Status"),
                "passenger_count": st.column_config.NumberColumn("Riders", format="%d"),
                
                # Turn the raw percentage into a visual progress bar right in the table!
                "utilization_pct": st.column_config.ProgressColumn(
                    "Capacity Utilization",
                    help="Current passenger load vs maximum train capacity",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "distance_from_start_km": st.column_config.NumberColumn("Pos (km)", format="%.1f")
            },
            hide_index=True,
            use_container_width=True
        )


    def render_headway_monitor(self):
        st.subheader("📏 Route Headway & Spacing")

        if self.headway_df.empty:
            st.info("Insufficient data to calculate headways.")
            return

        st.dataframe(
            self.headway_df,
            column_config={
                "train_id": st.column_config.TextColumn("Train"),
                "route_id": st.column_config.NumberColumn("Route", format="%d"),
                "train_ahead_id": st.column_config.TextColumn("Train Ahead"),
                "gap_km": st.column_config.NumberColumn("Distance Gap (km)", format="%.2f"),
                "spacing_health": st.column_config.TextColumn("Network Health"),
            },
            hide_index=True,
            use_container_width=True
        )

    def render_wait_times(self):
        st.subheader("Service Quality: Wait Times")
        
        if self.wait_time_df.empty:
            st.info("No wait time data available.")
            return

        # Smart Y-Axis Scaling to prevent violent jumping
        current_max = self.wait_time_df['wait_time'].max()
        # Ensure the Y-axis is always at least 20. If max goes over 20, give it 20% breathing room.
        y_max = max(20, current_max + (current_max * 0.2))

        # Build the vertical bar chart
        chart = alt.Chart(self.wait_time_df).mark_bar(
            cornerRadiusTopLeft=4, 
            cornerRadiusTopRight=4,
            size=60 # Make the bars nice and thick
        ).encode(
            x=alt.X('metric:N', sort=['Max', 'Avg', 'Min'], title=None, axis=alt.Axis(labelAngle=0, labelFontSize=14)),
            y=alt.Y('wait_time:Q', title="Wait Time (Ticks)", scale=alt.Scale(domain=[0, y_max])),
            color=alt.Color('metric:N', legend=None, scale=alt.Scale(
                domain=['Max', 'Avg', 'Min'],
                range=['#FF4B4B', '#FFAA00', '#21C354'] # Red for Max, Orange for Avg, Green for Min
            )),
            tooltip=['metric', 'wait_time']
        ).properties(
            height=300
        )
        
        st.altair_chart(chart, use_container_width=True, theme=None)
    
    def render_network_map(self):
        st.subheader("🕸️ Network Topology")
        
        # if self.map_df.empty:
        #     st.warning("No network topology found.")
        #     return

        # # 1. Dynamically generate evenly spaced colors!
        # unique_routes = sorted(self.map_df['route_id'].unique())
        # num_routes = max(len(unique_routes), 1) # Prevent division by zero just in case
        
        # route_colors = {}
        # for i, route in enumerate(unique_routes):
        #     # Divide the color wheel evenly
        #     hue = i / num_routes
        #     # Convert HSV to RGB (0.8 Saturation and 0.9 Value keeps them bright and punchy)
        #     r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        #     # Format as a standard #RRGGBB hex string for Graphviz
        #     route_colors[route] = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

        # # 2. Build Graphviz Dot Code
        # dot_code = 'digraph transit_map {\n'
        # dot_code += '  rankdir="LR";\n' 
        # dot_code += '  node [shape=box, style=filled, fillcolor="white", color="#444", fontname="sans-serif", margin="0.2,0.1"];\n'
        # dot_code += '  edge [penwidth=3];\n'
        # dot_code += '  graph [splines=ortho];\n' # Threw in that 90-degree subway aesthetic for you!

        # # 3. Draw the connections
        # for _, row in self.map_df.iterrows():
        #     route = row['route_id']
        #     color = route_colors.get(route, "#888888")
        #     start = row['station_name']
        #     end = row['next_station_name']
            
        #     dot_code += f'  "{start}" -> "{end}" [color="{color}", tooltip="Route {route}"];\n'
            
        # dot_code += '}'

        # st.graphviz_chart(dot_code, use_container_width=True)
    
    def run(self):
        self.fetch_world_clock()
        self.fetch_kpis()
        self.fetch_station_crowding_status()
        self.fetch_fleet_status()
        self.fetch_static_map()
        self.fetch_headways()
        self.fetch_wait_times()
        self.render_header()
        self.render_kpis()
        self.render_content_area()


if __name__ == "__main__":
    dashboard = TransitDashboard()
    dashboard.run()
