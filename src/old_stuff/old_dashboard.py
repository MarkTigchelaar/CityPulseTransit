import time
import pandas as pd
import streamlit as st
import altair as alt
from sqlalchemy import create_engine

# --- Configuration ---
DB_CONNECTION = "postgresql://thomas:mind_the_gap@localhost:5432/subway_system"
REFRESH_SECONDS = 1

# --- Page Setup ---
st.set_page_config(
    page_title="CityPulse Transit",
    page_icon="🚄",
    layout="wide"
)

# --- Database Connection ---
@st.cache_resource
def get_engine():
    return create_engine(DB_CONNECTION)

engine = get_engine()

# --- Load Data Functions ---
def load_train_activity():
    try:
        # reading from the View we created
        query = """
            SELECT station_name, total_visits, last_seen_tick 
            FROM public_transit.train_activity 
            ORDER BY total_visits DESC
        """
        return pd.read_sql(query, engine)
    except Exception as e:
        return pd.DataFrame()

def load_raw_logs():
    try:
        # reading raw logs for debugging view
        query = """
            SELECT * FROM public_transit.raw_train_status 
            ORDER BY clock_tick DESC 
            LIMIT 50
        """
        return pd.read_sql(query, engine)
    except Exception as e:
        return pd.DataFrame()

# --- Sidebar Controls ---
st.sidebar.title("🎮 Control Panel")

# The View Selector (Method 2)
view_mode = st.sidebar.radio(
    "Select Dashboard View:",
    ["Overview", "Station Traffic", "System Health", "Raw Data Log"]
)

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Live Auto-Refresh", value=True)

# --- Main Page Layout ---
st.title("🚄 CityPulse Transit Operations")

# Placeholders for dynamic content
kpi_container = st.container()
chart_container = st.empty()

# --- The "Game Loop" ---
while True:
    # 1. Load the primary dataset (used for KPIs)
    df_activity = load_train_activity()
    
    # 2. Render KPIs (Always visible at top)
    if not df_activity.empty:
        with kpi_container:
            # We use a container so these overwrite themselves cleanly
            k1, k2, k3 = st.columns(3)
            
            total_visits = df_activity['total_visits'].sum()
            busiest = df_activity.iloc[0]['station_name']
            active_stations = len(df_activity)

            k1.metric("Total Station Stops", total_visits)
            k2.metric("Busiest Station", busiest)
            k3.metric("Active Stations", active_stations)

    # 3. Render the Selected View
    with chart_container.container():
        
        # --- VIEW 1: Overview (Simple Metrics) ---
        if view_mode == "Overview":
            st.subheader("System Overview")
            if not df_activity.empty:
                st.bar_chart(df_activity.set_index("station_name")["total_visits"], color="#FF4B4B")
            else:
                st.info("Waiting for data...")

        # --- VIEW 2: Station Traffic (Detailed) ---
        elif view_mode == "Station Traffic":
            st.subheader("🚦 Station Traffic Analysis")
            if not df_activity.empty:
                # Example: Using Altair for a more custom chart (Optional upgrade)
                c = alt.Chart(df_activity).mark_bar().encode(
                    x=alt.X('station_name', sort='-y'),
                    y='total_visits',
                    color=alt.value("#3498db"),
                    tooltip=['station_name', 'total_visits', 'last_seen_tick']
                ).interactive()
                st.altair_chart(c, use_container_width=True)

        # --- VIEW 3: System Health (Placeholder) ---
        elif view_mode == "System Health":
            st.subheader("❤️ System Health")
            st.warning("🚧 Passenger Delays & Train Maintenance metrics coming soon...")
            
            # You could add a metric here for "Messages per second" from Kafka later

        # --- VIEW 4: Raw Logs (Debugging) ---
        elif view_mode == "Raw Data Log":
            st.subheader("📜 Live Event Log (Last 50)")
            df_logs = load_raw_logs()
            st.dataframe(df_logs, use_container_width=True, hide_index=True)

    # 4. Loop Logic
    if not auto_refresh:
        break
    
    time.sleep(REFRESH_SECONDS)
    st.rerun()