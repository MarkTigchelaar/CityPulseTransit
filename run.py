import subprocess
import sys
import time
import signal
import os
import psycopg2
from src.config import (
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    HOST_NAME,
    POSTGRES_PORT,
    DB_SCHEMA
)

processes = []

def cleanup(signum=None, frame=None):
    print("\n[CLEANUP] Shutting down all services gracefully...")
    for p in processes:
        if p.poll() is None:
            try:
                if sys.platform == 'win32':
                    # Windows shutdown
                    p.send_signal(signal.CTRL_BREAK_EVENT)
                    p.terminate()
                else:
                    # POSIX (Linux/Mac) shutdown
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception:
                pass  # Process might have already died

    print("[CLEANUP] System Offline. State is safely parked.")
    sys.exit(0)


# A clock tick in the simulation can be interrupted
# before all components update the db.
# This is data corruption
# Trimming off the state of the last 2 clock ticks eliminates
# the potential of this occurring.
def trim_latest_clock_ticks():
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=HOST_NAME,
            port=POSTGRES_PORT,
        )
        cur = conn.cursor()

        trimming_query = f"""
            DELETE
            FROM
                {DB_SCHEMA}.runtime_world_clock_state
            WHERE
                clock_tick >= (
                SELECT 
                    MAX(clock_tick) - 1
                FROM
                    {DB_SCHEMA}.runtime_world_clock_state
            );
        """
        cur.execute(trimming_query)
        deleted_rows = cur.rowcount
        conn.commit()

        cur.close()
        conn.close()

        if deleted_rows > 0:
            print("Successfully removed the most recent tick.")
        else:
            print("Clock table is empty.")

    except Exception as e:
        print(f"Could not trim clock tick (first run?): {e}")


def main():
    # Register the 'Ctrl+C' handler AND Docker's Stop handler
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("🚂 CityPulse Transit System Initializing...")
    trim_latest_clock_ticks()

    # Cross-platform kwargs for process grouping
    popen_kwargs = {}
    if sys.platform == 'win32':
        popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs['preexec_fn'] = os.setsid

    print("-> Starting Kafka Consumer...")
    p_consumer = subprocess.Popen(
        [sys.executable, "-m", "src.streaming.consumer"],
        cwd=os.getcwd(),
        **popen_kwargs
    )
    processes.append(p_consumer)
    time.sleep(3)
    
    print("-> Starting Train Simulation...")
    p_producer = subprocess.Popen(
        [sys.executable, "-m", "src.simulation.transit_system"], 
        cwd=os.getcwd(), 
        **popen_kwargs
    )
    processes.append(p_producer)

    print("-> Launching Dashboard...")
    p_dashboard = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "src/dashboard/dashboard.py", "--server.headless=true"],
        cwd=os.getcwd(),
        stdout=subprocess.DEVNULL,
        **popen_kwargs
    )
    processes.append(p_dashboard)

    print("-> Serving dbt Documentation...")
    # Note: On Windows, dbt is usually a command-line executable, so we use shell=True 
    # if it's not explicitly run through the python executable
    dbt_cmd = ["dbt", "docs", "serve", "--port", "8081", "--no-browser"]
    if sys.platform == 'win32':
        # Safest way to run command line tools on Windows subprocess
        dbt_cmd = ["cmd.exe", "/c"] + dbt_cmd

    p_docs = subprocess.Popen(
        dbt_cmd,
        cwd=os.path.join(os.getcwd(), "dbt"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **popen_kwargs
    )
    processes.append(p_docs)

    print("\n" + "=" * 50)
    print("SYSTEM ONLINE AND RUNNING")
    print("Live Dashboard: http://localhost:8501")
    print("dbt Dictionary: http://localhost:8081")
    print("Kafka Dashboard:   http://localhost:8080")
    print("Press Ctrl+C to safely stop the simulation.")
    print("=" * 50 + "\n")

    try:
        while True:
            time.sleep(1)
            if p_producer.poll() is not None:
                print("\nSimulation process ended cleaning up...")
                cleanup()
    except KeyboardInterrupt:
        pass  # Caught by the signal handler, do nothing


if __name__ == "__main__":
    main()