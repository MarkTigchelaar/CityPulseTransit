import time
import pandas as pd
import streamlit as st
import altair as alt
from sqlalchemy import create_engine

# --- Configuration ---
DB_CONNECTION = "postgresql://thomas:mind_the_gap@localhost:5432/subway_system"
REFRESH_SECONDS = 2  # Slightly slower to allow for rendering

TITLE = "City Pulse Transit Dashboard"

st.set_page_config(
    page_title=TITLE,
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for "Dark Mode" feel ---
st.markdown("""
<style>
    .metric-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #41424C;
    }
</style>
""", unsafe_allow_html=True)

# --- Database Connection ---
@st.cache_resource
def get_engine():
    return create_engine(DB_CONNECTION)

engine = get_engine()

# --- Data Loaders ---
def load_fleet_status(tick):
    try:
        return pd.read_sql(f"SELECT * FROM public_transit.live_fleet_status where clock_tick > {tick - 50}", engine)
    except: return pd.DataFrame()

def load_station_congestion(tick):
    try:
        return pd.read_sql(f"SELECT * FROM public_transit.live_station_congestion where clock_tick > {tick - 50}", engine)
    except: return pd.DataFrame()

def load_route_topology():
    try:
        return pd.read_sql("SELECT * FROM public_transit.route_topology", engine)
    except: return pd.DataFrame()

def load_clock():
    try:
        return pd.read_sql("SELECT * FROM public_transit.runtime_world_clock_state ORDER BY clock_tick DESC LIMIT 1", engine)
    except: return pd.DataFrame()


def convert_day_code_to_day(day_code: str) -> str:
    day = "Error"
    match day_code:
        case 'M':
            day = "Monday"
        case 'T':
            day = "Tuesday"
        case 'W':
            day = "Wednesday"
        case 'R':
            day = "Thursday"
        case 'F':
            day = "Friday"
        case 'S':
            day = "Saturday"
        case 'U':
            day = "Sunday"
        case _:
            raise Exception(f"Unknown day code {day_code}")
    return day
        
# --- Sidebar ---
st.sidebar.title("🎛️ Ops Control")
selected_route = st.sidebar.selectbox("Filter Route Map", [1, 2, 3, "All"], index=3)

# --- Header / KPI Row ---
st.title(TITLE)

# --- Main Logic Loop ---
placeholder = st.empty()

while True:
    with placeholder.container():
        clock_df = load_clock()
        tick = None
        if not clock_df.empty:
            tick = clock_df.iloc[0]['clock_tick']
            day = convert_day_code_to_day(clock_df.iloc[0]['day_of_week'])
            hour = clock_df.iloc[0]['hour_of_day']
            st.markdown(f"### 🕒 {day} | {hour:02d}:00 | Tick: {tick}")
        else:
            st.markdown("### 🕒 System Offline")
        # Load Fresh Data
        df_fleet = load_fleet_status(tick)
        df_stations = load_station_congestion(tick)
        df_topo = load_route_topology()

        df_fleet['station_id'] = pd.to_numeric(df_fleet['station_id'], errors='coerce')


        df_stations['station_id'] = pd.to_numeric(df_stations['station_id'], errors='coerce')

        df_fleet = df_fleet[df_fleet['clock_tick'] == tick]


        df_fleet = df_fleet.drop_duplicates(subset=['train_id'])

        if df_fleet.empty or df_stations.empty:
            st.warning("Waiting for simulation data... (Run `python src/transit_system.py`)")
            time.sleep(2)
            continue

        # --- KPI Row ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_pax = df_fleet['passenger_count'].sum()
        avg_util = df_fleet['utilization_pct'].mean()
        active_trains = len(df_fleet[df_fleet['status'] != 'Idle'])
        crowded_station = df_stations.iloc[0]['station_name'] if not df_stations.empty else "N/A"

        kpi1.metric("👥 Total Pax on Board", f"{total_pax}")
        kpi2.metric("📊 Avg Fleet Utilization", f"{avg_util:.1f}%")
        kpi3.metric("🚄 Active Trains", f"{active_trains}")
        kpi4.metric("🔥 Crowded Station", crowded_station)

        st.markdown("---")

        # --- ROW 2: The "Live Route Map" (The Cool Part) ---
        st.subheader("📍 Live Network Velocity")
        
        # 1. Join Fleet Data with Topology to get X/Y coordinates for plotting
        if not df_topo.empty:
            # Filter topology if specific route selected
            if selected_route != "All":
                df_topo_filtered = df_topo[df_topo['route_id'] == int(selected_route)]
                df_fleet_filtered = df_fleet[df_fleet['route_id'] == int(selected_route)]
            else:
                df_topo_filtered = df_topo
                df_fleet_filtered = df_fleet

            # Base Layer: The Rail Lines (Gray lines connecting stations)
            lines = alt.Chart(df_topo_filtered).mark_line(color='gray', opacity=0.5, size=5).encode(
                x=alt.X('linear_distance_km', title='Distance (km)'),
                y=alt.Y('route_id:O', title='Route'),
                detail='route_id'
            )

            # Station Layer: White dots
            stations = alt.Chart(df_topo_filtered).mark_circle(size=100, color='white', opacity=0.8).encode(
                x='linear_distance_km',
                y='route_id:O',
                tooltip=['station_name', 'route_id']
            )

            # Train Layer: Colored Triangles (mapped roughly to station location for now)
            # In V2, we would join on segment_id to interpolate exact position
            # For now, we map train->station->distance
            df_train_pos = df_fleet_filtered.merge(
                df_topo_filtered[['station_id', 'route_id', 'linear_distance_km']], 
                on=['station_id', 'route_id'], 
                how='left'
            )
            # Fallback for trains between stations (keep them on the chart)
            df_train_pos['linear_distance_km'] = df_train_pos['linear_distance_km'].fillna(0)

            trains = alt.Chart(df_train_pos).mark_point(shape='triangle-right', size=200, filled=True).encode(
                x='linear_distance_km',
                y='route_id:O',
                color=alt.Color('utilization_pct', scale=alt.Scale(scheme='redyellowgreen', domain=[100, 0]), title='Load %'),
                tooltip=['train_id', 'speed', 'passenger_count', 'status']
            )

            # Combine Layers
            network_map = (lines + stations + trains).properties(height=300).interactive()
            st.altair_chart(network_map, use_container_width=True)

        # --- ROW 3: Deep Dives ---
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("🌡️ Station Crowd Meter")
            
            crowd_chart = alt.Chart(df_stations).mark_bar().encode(
                x=alt.X('passengers_waiting', title='Pax Waiting'),
                y=alt.Y('station_name', sort='-x'),
                color=alt.Color('passengers_waiting', scale=alt.Scale(scheme='inferno')),
                tooltip=['passengers_waiting', 'total_passengers_in_station']
            ).properties(height=300)
            
            st.altair_chart(crowd_chart, use_container_width=True)

        with col_right:
            st.subheader("🏗️ Fleet Capacity Matrix")
            
            # Scatter plot: Capacity vs Pax Count
            cap_chart = alt.Chart(df_fleet).mark_circle(size=150).encode(
                x=alt.X('max_capacity', title='Total Capacity'),
                y=alt.Y('passenger_count', title='Pax on Board'),
                color='route_id:N',
                tooltip=['train_id', 'route_id', 'utilization_pct']
            ).properties(height=300)
            
            st.altair_chart(cap_chart, use_container_width=True)
            
        # --- ROW 4: Raw Data Expander ---
        with st.expander("🔎 Inspect Raw Telemetry"):
            st.dataframe(df_fleet)


    time.sleep(REFRESH_SECONDS)
    st.rerun()