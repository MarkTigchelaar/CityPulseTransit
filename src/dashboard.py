import time
import pandas as pd
import streamlit as st
import altair as alt
from sqlalchemy import create_engine

# --- Configuration ---
DB_CONNECTION = "postgresql://thomas:mind_the_gap@localhost:5432/subway_system"
REFRESH_SECONDS = 2.0  # Increased to prevent browser crash (race conditions)

TITLE = "City Pulse Transit Dashboard"

st.set_page_config(
    page_title=TITLE,
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
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
        # Fetch slightly more history to ensure we catch the current tick
        query = f"SELECT * FROM public_transit.live_fleet_status WHERE clock_tick >= {tick - 5}"
        return pd.read_sql(query, engine)
    except Exception:
        return pd.DataFrame()

def load_station_congestion(tick):
    try:
        return pd.read_sql(f"SELECT * FROM public_transit.live_station_congestion WHERE clock_tick >= {tick - 5}", engine)
    except Exception:
        return pd.DataFrame()

# Cache static data, but DEDUP it immediately
@st.cache_data
def load_route_topology():
    try:
        df = pd.read_sql("SELECT * FROM public_transit.route_topology", engine)
        # CRITICAL FIX: Remove duplicate station entries to prevent "Ghost Trains" during merge
        return df.drop_duplicates(subset=['station_id', 'route_id'])
    except Exception:
        return pd.DataFrame()

def load_clock():
    try:
        return pd.read_sql("SELECT * FROM public_transit.runtime_world_clock_state ORDER BY clock_tick DESC LIMIT 1", engine)
    except Exception:
        return pd.DataFrame()

def convert_day_code_to_day(day_code: str) -> str:
    days = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 'R': 'Thursday', 'F': 'Friday', 'S': 'Saturday', 'U': 'Sunday'}
    return days.get(day_code, "Unknown")

# --- Sidebar ---
st.sidebar.title("🎛️ Ops Control")
selected_route = st.sidebar.selectbox("Filter Route Map", [1, 2, 3, "All"], index=3)

# --- Header ---
st.title(TITLE)

# --- Main Logic ---

# 1. Get Time
clock_df = load_clock()
if not clock_df.empty:
    tick = int(clock_df.iloc[0]['clock_tick'])
    day = convert_day_code_to_day(clock_df.iloc[0]['day_of_week'])
    hour = int(clock_df.iloc[0]['hour_of_day'])
    st.markdown(f"### 🕒 {day} | {hour:02d}:00 | Tick: {tick}")
else:
    tick = 0
    st.markdown("### 🕒 System Offline")

# 2. Load Data
# Use deep copy on cached data to prevent thread-safety errors
df_topo = load_route_topology().copy(deep=True)
df_fleet = load_fleet_status(tick)
df_stations = load_station_congestion(tick)

# 3. Data Processing & Ghost Busting
if not df_fleet.empty:
    # Ensure types match for merging
    df_fleet['station_id'] = pd.to_numeric(df_fleet['station_id'], errors='coerce')
    
    # STRICT FILTER: Only show the exact current tick
    df_fleet = df_fleet[df_fleet['clock_tick'] == tick]
    
    # GHOST BUSTER: If the DB has duplicates for the same train/tick, keep the last one.
    # If 'created_at' exists, use it to find the newest. Otherwise, trust the DB order.
    if 'created_at' in df_fleet.columns:
        df_fleet = df_fleet.sort_values('created_at')
    
    df_fleet = df_fleet.drop_duplicates(subset=['train_id'], keep='last')

if not df_stations.empty:
    df_stations['station_id'] = pd.to_numeric(df_stations['station_id'], errors='coerce')
    # Filter stations to current tick as well
    df_stations = df_stations[df_stations['clock_tick'] == tick]
    df_stations = df_stations.drop_duplicates(subset=['station_id'], keep='last')

# 4. Wait State
if df_fleet.empty or df_stations.empty:
    st.warning(f"Waiting for data synchronization (Tick: {tick})...")
    time.sleep(2)
    st.rerun()

# --- KPI Row ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_pax = int(df_fleet['passenger_count'].sum())
avg_util = df_fleet['utilization_pct'].mean()
active_trains = len(df_fleet[df_fleet['status'] != 'Idle'])
crowded_station = df_stations.sort_values('passengers_waiting', ascending=False).iloc[0]['station_name'] if not df_stations.empty else "N/A"

kpi1.metric("👥 Total Pax on Board", f"{total_pax}")
kpi2.metric("📊 Avg Fleet Utilization", f"{avg_util:.1f}%")
kpi3.metric("🚄 Active Trains", f"{active_trains}")
kpi4.metric("🔥 Crowded Station", crowded_station)

st.markdown("---")

# --- ROW 2: The "Live Route Map" ---
st.subheader("📍 Live Network Velocity")

if not df_topo.empty:
    # Filter topology
    if selected_route != "All":
        df_topo_filtered = df_topo[df_topo['route_id'] == int(selected_route)].copy(deep=True)
        df_fleet_filtered = df_fleet[df_fleet['route_id'] == int(selected_route)].copy(deep=True)
    else:
        df_topo_filtered = df_topo.copy(deep=True)
        df_fleet_filtered = df_fleet.copy(deep=True)

    # Base Layer: Lines
    lines = alt.Chart(df_topo_filtered).mark_line(color='gray', opacity=0.5, size=5).encode(
        x=alt.X('linear_distance_km', title='Distance (km)'),
        y=alt.Y('route_id:O', title='Route'),
        detail='route_id'
    )

    # Station Layer: Dots
    stations = alt.Chart(df_topo_filtered).mark_circle(size=100, color='white', opacity=0.8).encode(
        x='linear_distance_km',
        y='route_id:O',
        tooltip=['station_name', 'route_id']
    )

    # Train Layer: Triangles
    # Merge fleet with topology to get positions
    df_train_pos = df_fleet_filtered.merge(
        df_topo_filtered[['station_id', 'route_id', 'linear_distance_km']], 
        on=['station_id', 'route_id'], 
        how='left'
    )
    
    # Fill missing distances (moving trains) to 0 or keep them distinct
    # Ideally, we would use segment_id for moving trains, but for now we fallback
    df_train_pos['linear_distance_km'] = df_train_pos['linear_distance_km'].fillna(0)

    trains = alt.Chart(df_train_pos).mark_point(shape='triangle-right', size=200, filled=True).encode(
        x='linear_distance_km',
        y='route_id:O',
        color=alt.Color('utilization_pct', scale=alt.Scale(scheme='redyellowgreen', domain=[100, 0]), title='Load %'),
        tooltip=['train_id', 'speed', 'passenger_count', 'status']
    )

    network_map = (lines + stations + trains).properties(height=300).interactive()
    st.altair_chart(network_map, use_container_width=True)

# --- ROW 3: Deep Dives ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🌡️ Station Crowd Meter")
    
    # Explicit copy to avoid mutation errors
    chart_data_crowd = df_stations.copy(deep=True)
    
    crowd_chart = alt.Chart(chart_data_crowd).mark_bar().encode(
        x=alt.X('passengers_waiting', title='Pax Waiting'),
        y=alt.Y('station_name', sort='-x'),
        color=alt.Color('passengers_waiting', scale=alt.Scale(scheme='inferno')),
        tooltip=['passengers_waiting', 'total_passengers_in_station']
    ).properties(height=300)
    
    st.altair_chart(crowd_chart, use_container_width=True)

with col_right:
    st.subheader("🏗️ Fleet Capacity Matrix")
    
    chart_data_fleet = df_fleet.copy(deep=True)
    
    cap_chart = alt.Chart(chart_data_fleet).mark_circle(size=150).encode(
        x=alt.X('max_capacity', title='Total Capacity'),
        y=alt.Y('passenger_count', title='Pax on Board'),
        color='route_id:N',
        tooltip=['train_id', 'route_id', 'utilization_pct']
    ).properties(height=300)
    
    st.altair_chart(cap_chart, use_container_width=True)
    
# --- ROW 4: Raw Data ---
with st.expander("🔎 Inspect Raw Telemetry"):
    st.dataframe(df_fleet)

# --- AUTO REFRESH ---
time.sleep(REFRESH_SECONDS)
st.rerun()