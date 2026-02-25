import math
import colorsys
import pandas as pd
from typing import Any
import streamlit as st
import altair as alt
from streamlit_autorefresh import st_autorefresh

from data_service import DataService

REFRESH_SECONDS = 2


st_autorefresh(interval=1000, limit=None, key="city_pulse_refresher")


class TransitDashboard:
    def __init__(self):
        self.title = "City Pulse Transit Dashboard"
        self.data_service = DataService()

    def render_header(self):
        st.title(self.title)
        clock_df = self.data_service.fetch_world_clock()
        if not clock_df.empty:
            row = clock_df.iloc[0]
            year = int(row["year"])
            hour = int(row["hour_of_day"])
            minute = int(row["minute"])
            day_name = row["day_name"]
            month_name = row["month_name"]
            day_of_month = int(row["day_of_month"])

            st.markdown(
                f"### 🕒 {day_name}, {month_name} {day_of_month}, {year} | {hour:02d}:{minute:02d}"
            )
        else:
            st.markdown("### 🕒 System Offline")

    def render_kpis(self):
        kpi_df = self.data_service.fetch_kpis()
        if kpi_df.empty:
            return

        kpis = kpi_df.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            label="Total in System",
            value=int(kpis["total_passengers_in_system"]),
            help="The total number of passengers currently tracked anywhere in the network (riding + waiting).",
        )

        col2.metric(
            label="Passengers Riding",
            value=int(kpis["total_passengers_riding"]),
            help="Passengers currently onboard an active train.",
        )

        col3.metric(
            label="Passengers Waiting",
            value=int(kpis["total_passengers_waiting"]),
            help="Passengers standing on platforms waiting for a train to arrive.",
        )

        col4.metric(
            label="Network Utilization",
            value=f"{kpis['avg_network_utilization_pct']}%",
            help="The average capacity utilization across all active trains.",
        )

        st.markdown("---")

    def render_content_area(self):
        (
            tab_map,
            tab_matrix,
            tab_network,
            tab_crowd,
            tab_bunching,
            tab_service_quality,
        ) = st.tabs(
            [
                "Live Map",
                "Fleet Matrix",
                "System Map",
                "Crowd Meter",
                "Train bunching",
                "Service Quality",
            ]
        )
        with tab_map:
            self.render_live_map()
        with tab_matrix:
            self.render_fleet_matrix()
        with tab_network:
            self.render_network_map()
        with tab_crowd:
            self.render_crowd_meter()
        with tab_bunching:
            self.render_headway_monitor()
        with tab_service_quality:
            self.render_wait_times()

    def render_live_map(self):
        st.subheader("📍 Live Fleet Movement")

        fleet_df = self.data_service.fetch_fleet_status()
        topology_df = self.data_service.fetch_map_topology()

        if topology_df.empty:
            st.warning("No route topology data found.")
            return

        if fleet_df.empty:
            st.warning("No fleet data found.")
            return

        track_layer = self.make_track_layer()
        station_layer = self.make_station_layer()
        trains = self.make_train_layer()
        combined_chart = track_layer + station_layer + trains

        st.altair_chart(
            combined_chart.properties(height=300), use_container_width=True, theme=None
        )

    def get_live_map_max_km(self):
        track_df = self.data_service.fetch_track_df()
        return track_df["end_km"].max()

    def get_live_map_route_domain(self):
        topology_df = self.data_service.fetch_map_topology()
        return sorted(topology_df["route_id"].unique().tolist())

    def get_live_map_x_scale(self):
        system_max_km = self.get_live_map_max_km()
        return alt.Scale(domain=[0, system_max_km], nice=False)

    def get_live_map_y_scale(self):
        route_domain = self.get_live_map_route_domain()
        return alt.Scale(domain=route_domain)

    def make_track_layer(self):
        track_df = self.data_service.fetch_track_df()
        x_scale = self.get_live_map_x_scale()
        y_scale = self.get_live_map_y_scale()
        return (
            alt.Chart(track_df)
            .mark_rule(color="#444", strokeWidth=3)
            .encode(
                x=alt.X("start_km:Q", scale=x_scale, title="Distance (km)"),
                x2="end_km:Q",
                y=alt.Y("route_id:O", scale=y_scale, title="Route"),
            )
        )

    def make_station_layer(self):
        topology_df = self.data_service.fetch_map_topology()
        x_scale = self.get_live_map_x_scale()
        y_scale = self.get_live_map_y_scale()
        return (
            alt.Chart(topology_df)
            .mark_circle(size=100, color="white", opacity=1.0)
            .encode(
                x=alt.X("distance_from_start_km:Q", scale=x_scale),
                y=alt.Y("route_id:O", scale=y_scale),
                tooltip=["station_name", "distance_from_start_km"],
            )
        )

    def make_train_layer(self):
        fleet_df = self.data_service.fetch_fleet_status()
        system_max_km = self.get_live_map_max_km()
        plot_df = fleet_df.copy()
        plot_df["distance_from_start_km"] = plot_df["distance_from_start_km"].astype(
            float
        )
        plot_df["distance_from_start_km"] = plot_df["distance_from_start_km"].clip(
            upper=system_max_km
        )
        x_scale = self.get_live_map_x_scale()
        y_scale = self.get_live_map_y_scale()
        return (
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

    def render_crowd_meter(self):
        st.subheader("🌡️ Station Crowd Density")
        station_crowding_df = self.data_service.fetch_station_crowding_status()
        if station_crowding_df.empty:
            st.info("Awaiting passenger data...")
            return

        current_max = station_crowding_df["total_passengers_in_station"].max()
        y_max = current_max if pd.notna(current_max) and current_max > 0 else 10

        chart = (
            alt.Chart(station_crowding_df)
            .mark_bar()
            .encode(
                x=alt.X("station_name:N", sort="-y", title="Station"),
                y=alt.Y(
                    "total_passengers_in_station:Q",
                    title="Passengers Waiting",
                    scale=alt.Scale(domain=[0, y_max]),
                ),
                color=alt.Color("total_passengers_in_station:Q", legend=None),
            )
            .properties(height=300)
        )

        st.altair_chart(chart, use_container_width=True, theme=None)

    def render_fleet_matrix(self):
        st.subheader("🏗️ Fleet Status Matrix")
        fleet_df = self.data_service.fetch_fleet_status()
        if fleet_df.empty:
            st.info("No trains currently active in the network.")
            return

        st.divider()
        st.dataframe(
            fleet_df,
            column_config=self.fleet_matrix_column_config(),
            hide_index=True,
            use_container_width=True,
        )

    def fleet_matrix_column_config(self) -> dict[str, Any]:
        return {
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
            "distance_from_start_km": st.column_config.NumberColumn(
                "Pos (km)", format="%.1f"
            ),
        }

    def render_headway_monitor(self):
        st.subheader("📏 Route Headway & Spacing")
        headway_df = self.data_service.fetch_headway_status()
        if headway_df.empty:
            st.info("Insufficient data to calculate headways.")
            return

        st.dataframe(
            headway_df,
            column_config=self.headway_column_config(),
            hide_index=True,
            use_container_width=True,
        )

    def headway_column_config(self):
        return {
            "train_id": st.column_config.TextColumn("Train"),
            "route_id": st.column_config.NumberColumn("Route", format="%d"),
            "train_ahead_id": st.column_config.TextColumn("Train Ahead"),
            "gap_km": st.column_config.NumberColumn("Distance Gap (km)", format="%.2f"),
            "spacing_health": st.column_config.TextColumn("Network Health"),
        }

    def render_wait_times(self):
        st.subheader("Service Quality: Wait Times")
        wait_time_df = self.data_service.fetch_wait_times()
        if wait_time_df.empty:
            st.info("No wait time data available.")
            return
        current_max = wait_time_df["wait_time"].max()
        y_max = max(20, current_max + (current_max * 0.2))

        chart = (
            alt.Chart(wait_time_df)
            .mark_bar(
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4,
                size=60,
            )
            .encode(
                x=alt.X(
                    "metric:N",
                    sort=["Max", "Avg", "Min"],
                    title=None,
                    axis=alt.Axis(labelAngle=0, labelFontSize=14),
                ),
                y=alt.Y(
                    "wait_time:Q",
                    title="Wait Time (Ticks)",
                    scale=alt.Scale(domain=[0, y_max]),
                ),
                color=alt.Color(
                    "metric:N",
                    legend=None,
                    scale=alt.Scale(
                        domain=["Max", "Avg", "Min"],
                        range=[
                            "#FF4B4B",
                            "#FFAA00",
                            "#21C354",
                        ],
                    ),
                ),
                tooltip=["metric", "wait_time"],
            )
            .properties(height=300)
        )

        st.altair_chart(chart, use_container_width=True, theme=None)

    def render_network_map(self):
        st.subheader("🕸️ Network Topology")
        map_df = self.data_service.fetch_static_map()
        if map_df.empty:
            st.warning("No network topology found.")
            return

        # Orchestrate the helpers
        station_coords = self._get_station_coordinates()
        route_colors = self._generate_route_colors(map_df["route_id"].unique())
        svg_content = self._build_svg_network(map_df, station_coords, route_colors)

        st.markdown(
            f"<div style='display: flex; justify-content: center;'>{svg_content}</div>",
            unsafe_allow_html=True,
        )

    def _get_station_coordinates(self) -> dict:
        """Isolated geometry to easily swap with a database query later."""
        return {
            "Central Station": {"x": 100, "y": 200},
            "Northgate": {"x": 350, "y": 200},
            "South Commons": {"x": 600, "y": 200},
        }

    def _generate_route_colors(self, routes) -> dict:
        """Generates a stable, visually distinct color palette for routes."""
        route_colors = {}
        for i, route in enumerate(routes):
            hue = i / len(routes)
            r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
            route_colors[route] = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        return route_colors

    def _build_svg_network(self, map_df: pd.DataFrame, station_coords: dict, route_colors: dict) -> str:
        """Constructs the raw SVG string using vector math for parallel tracks."""
        # Using a list for string building is significantly cleaner and faster in Python
        svg_elements = [
            '<svg viewBox="0 0 700 400" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">'
        ]
        


        # --- Draw Edges Dynamically ---
        drawn_corridors = {} 
        for _, row in map_df.iterrows():
            start_name, end_name = row["station_name"], row["next_station_name"]
            route_id = row["route_id"]
            color = route_colors.get(route_id, "#888888")
            color_id = color.replace("#", "")

            if start_name not in station_coords or end_name not in station_coords:
                continue

            x1, y1 = station_coords[start_name]["x"], station_coords[start_name]["y"]
            x2, y2 = station_coords[end_name]["x"], station_coords[end_name]["y"]

            corridor = tuple(sorted([start_name, end_name]))
            drawn_corridors.setdefault(corridor, [])

            if route_id in drawn_corridors[corridor]:
                continue
            drawn_corridors[corridor].append(route_id)

            idx = len(drawn_corridors[corridor]) - 1
            offset_mag = 0 if idx == 0 else (12 if idx % 2 == 1 else -12) * ((idx + 1) // 2)

            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy)
            if length > 0:
                nx, ny = -dy / length, dx / length
                ox1, oy1 = x1 + (nx * offset_mag), y1 + (ny * offset_mag)
                ox2, oy2 = x2 + (nx * offset_mag), y2 + (ny * offset_mag)

                # Attach the arrow marker to the end of the line
                svg_elements.append(
                    f'  <line x1="{ox1:.1f}" y1="{oy1:.1f}" x2="{ox2:.1f}" y2="{oy2:.1f}" '
                    f'stroke="{color}" stroke-width="6" marker-end="url(#arrow-{color_id})" />'
                )

        # --- Draw Stations ---
        for name, coords in station_coords.items():
            cx, cy = coords["x"], coords["y"]
            svg_elements.append(
                f'  <circle cx="{cx}" cy="{cy}" r="8" fill="white" stroke="#444" stroke-width="3" />'
            )
            svg_elements.append(
                f'  <text x="{cx}" y="{cy - 20}" font-family="sans-serif" font-size="14" '
                f'font-weight="bold" text-anchor="middle" fill="#444">{name}</text>'
            )

        svg_elements.append("</svg>")
        return "\n".join(svg_elements)


    def run(self):
        self.render_header()
        self.render_kpis()
        self.render_content_area()


if __name__ == "__main__":
    dashboard = TransitDashboard()
    dashboard.run()
