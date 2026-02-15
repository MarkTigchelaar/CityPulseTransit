import subprocess
import sys
import time
import signal
import os

# Store processes globally so signal handler can find them
processes = []

# This used Gemini:
def cleanup(signum, frame):
    print("\nShutting down simulation...")
    for p in processes:
        if p.poll() is None:
            # Terminate gracefully
            p.terminate()
    print("Offline.")
    sys.exit(0)

def main():
    # Register the 'Ctrl+C' handler
    signal.signal(signal.SIGINT, cleanup)

    print("CityPulse Transit System...")

    print("Starting Kafka Consumer...")
    p_consumer = subprocess.Popen(
        [sys.executable, "src/consumer.py"],
        cwd=os.getcwd()
    )
    processes.append(p_consumer)
    time.sleep(2)


    print("Starting Train Simulation...")
    p_producer = subprocess.Popen(
        [sys.executable, "src/transit_system.py"],
        cwd=os.getcwd()
    )
    processes.append(p_producer)


    print("Launching Dashboard...")
    p_dashboard = subprocess.Popen(
        ["streamlit", "run", "src/dashboard.py"],
        cwd=os.getcwd()
    )
    processes.append(p_dashboard)

    print("\nPress Ctrl+C to stop.")
    p_dashboard.wait()

if __name__ == "__main__":
    main()