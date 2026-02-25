import subprocess
import sys
import time
import signal
import os
import psycopg2
from dotenv import load_dotenv

# Store processes globally so signal handler can find them
processes = []

def cleanup(signum=None, frame=None):
    print("\n[CLEANUP] Shutting down all services gracefully...")
    for p in processes:
        if p.poll() is None:
            try:
                # os.killpg kills the ENTIRE process group (no zombies left behind!)
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception as e:
                pass # Process might have already died
    
    print("[CLEANUP] System Offline. State is safely parked.")
    sys.exit(0)


def chop_latest_clock_tick():
    """
    Deletes the absolute latest clock tick from the world clock table.
    This forces the simulation to replay the last tick, safely overwriting 
    any partial data from a previous crash/ interrupt.
    """
    load_dotenv()
    print("✂️  Chopping the latest clock tick to force a safe replay...")
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "subway_system"),
            user=os.getenv("POSTGRES_USER", "thomas"),
            password=os.getenv("POSTGRES_PASSWORD", "mind_the_gap"),
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()
        
        chop_query = """
        DELETE FROM public_transit.runtime_world_clock_state
        WHERE clock_tick >= (SELECT MAX(clock_tick) - 1 FROM public_transit.runtime_world_clock_state);
        """
        cur.execute(chop_query)
        # Fetching how many rows were deleted (should be 1 or 0)
        deleted_rows = cur.rowcount
        conn.commit()
        
        cur.close()
        conn.close()
        
        if deleted_rows > 0:
            print("✅ Successfully removed the most recent tick. Ready for replay.")
        else:
            print("ℹ️ Clock table is empty. Starting fresh.")
            
    except Exception as e:
        print(f"⚠️ Could not chop clock tick (first run?): {e}")

def main():
    # Register the 'Ctrl+C' handler AND Docker's Stop handler
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("🚂 CityPulse Transit System Initializing...")

    print("-> Starting Kafka Consumer...")
    p_consumer = subprocess.Popen(
        [sys.executable, "src/consumer.py"],
        cwd=os.getcwd(),
        preexec_fn=os.setsid  # Creates a strict process group boundary
    )
    processes.append(p_consumer)
    time.sleep(3) # Give Kafka a head start
    chop_latest_clock_tick()

    print("-> Starting Train Simulation...")
    p_producer = subprocess.Popen(
        [sys.executable, "src/transit_system.py"],
        cwd=os.getcwd(),
        preexec_fn=os.setsid
    )
    processes.append(p_producer)

    print("-> Launching Dashboard...")
    p_dashboard = subprocess.Popen(
        ["streamlit", "run", "src/dashboard.py", "--server.headless=true"],
        cwd=os.getcwd(),
        preexec_fn=os.setsid,
        stdout=subprocess.DEVNULL # Keeps Streamlit from cluttering your terminal
    )
    processes.append(p_dashboard)

    print("-> Serving dbt Documentation...")
    p_docs = subprocess.Popen(
        ["dbt", "docs", "serve", "--port", "8081", "--no-browser"],
        cwd=os.path.join(os.getcwd(), "dbt"), # Ensure it runs in the dbt folder
        preexec_fn=os.setsid,
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )
    processes.append(p_docs)

    print("\n" + "="*50)
    print("🚀 SYSTEM ONLINE AND RUNNING")
    print("📊 Live Dashboard: http://localhost:8501")
    print("📚 dbt Dictionary: http://localhost:8081")
    print("Kafka Dashboard:   http://localhost:8080")
    print("Press Ctrl+C to safely stop the simulation.")
    print("="*50 + "\n")

    try:
        while True:
            time.sleep(1)
            if p_producer.poll() is not None:
                print("\nSimulation process ended cleaning up...")
                cleanup()
    except KeyboardInterrupt:
        pass # Caught by the signal handler, do nothing

if __name__ == "__main__":
    main()
