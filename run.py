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
    #p_producer.wait()


    print("Launching Dashboard...")
    p_dashboard = subprocess.Popen(
        ["streamlit", "run", "src/dashboard.py", "--server.headless=true"],
        cwd=os.getcwd()
    )
    processes.append(p_dashboard)

    print("\nPress Ctrl+C to stop.")
    p_dashboard.wait()

if __name__ == "__main__":
    main()


# class SimulationRunner:
#     def __init__(self):
#         self.running = True
#         # 1. Bind the "Kill Signals" (Ctrl+C from keyboard, Stop from Docker)
#         signal.signal(signal.SIGINT, self.shutdown)
#         signal.signal(signal.SIGTERM, self.shutdown)

#     def shutdown(self, signum, frame):
#         """
#         This runs when you hit Ctrl+C.
#         """
#         print(f"\n[STOP] Received signal {signum}. Stopping gracefully...")
#         self.running = False

#     def run(self):
#         print("[START] Simulation starting...")
        
#         # 2. The Main Loop checks 'self.running' instead of 'True'
#         while self.running:
#             try:
#                 # --- YOUR SIMULATION LOGIC HERE ---
#                 self.ti__ck() 
#                 time.sleep(1) # or whatever your sleep is
#                 # ----------------------------------
#             except Exception as e:
#                 print(f"[ERROR] Crash: {e}")
#                 self.cleanup()
#                 sys.exit(1)
        
#         # 3. Loop exited? Run cleanup!
#         self.cleanup()

#     def cleanup(self):
#         """
#         The critical part: Tell the DB we are stopped.
#         """
#         print("[CLEANUP] updating system state to 'STOPPED'...")
        
#         # TODO: Run your SQL update here
#         # UPDATE system_state SET is_running = false, status = 'STOPPED' WHERE ...
        
#         # TODO: Close Kafka producers / DB connections if needed
        
#         print("[DONE] System is safe to restart.")
#         sys.exit(0)

# if __name__ == "__main__":
#     sim = SimulationRunner()
#     sim.run()