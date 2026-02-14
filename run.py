import subprocess
import sys
import time
import signal
import os

# Store processes globally so signal handler can find them
processes = []

def cleanup(signum, frame):
    """Catches Ctrl+C and kills all subprocesses."""
    print("\n🛑 Shutting down simulation...")
    for p in processes:
        # Check if process is still running
        if p.poll() is None:
            # Terminate gracefully
            p.terminate()
            # If on Windows, we might need to force kill the tree if terminate fails
            # but terminate() is usually sufficient for Python scripts.
    
    print("✅ All systems offline.")
    sys.exit(0)

def main():
    # Register the 'Ctrl+C' handler
    signal.signal(signal.SIGINT, cleanup)

    print("🚄 CityPulse Transit System Starting...")
    print("---------------------------------------")

    # 1. Start the Consumer (ETL)
    print("🔌 Starting Kafka Consumer...")
    p_consumer = subprocess.Popen(
        [sys.executable, "src/consumer.py"],
        cwd=os.getcwd()
    )
    processes.append(p_consumer)
    time.sleep(2) # Give it a moment to connect

    # 2. Start the Simulation (Producer)
    print("🚂 Starting Train Simulation...")
    p_producer = subprocess.Popen(
        [sys.executable, "src/transit_system.py"],
        cwd=os.getcwd()
    )
    processes.append(p_producer)

    # 3. Start the Dashboard
    print("📊 Launching Dashboard...")
    # Streamlit needs to be run as a module ('streamlit run')
    p_dashboard = subprocess.Popen(
        ["streamlit", "run", "src/dashboard.py"],
        cwd=os.getcwd()
    )
    processes.append(p_dashboard)

    print("\n✅ System Running! Press Ctrl+C to stop everything.")
    
    # Keep the main script alive so it can catch the Ctrl+C
    # We wait on the dashboard process; if you close the dashboard browser tab/server, script ends.
    p_dashboard.wait()

if __name__ == "__main__":
    main()