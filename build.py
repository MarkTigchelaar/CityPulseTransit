import os
import subprocess
import sys
import time

def run_command(command, desc):
    print(f"🔨 {desc}...")
    try:
        subprocess.check_call(command, shell=True)
        print(f"✅ {desc} Complete!\n")
    except subprocess.CalledProcessError:
        print(f"❌ Error during: {desc}")
        sys.exit(1)
def run_dbt_command(command, desc):
    """
    Finds the dbt project folder, switches to it, runs the command, 
    and switches back safely.
    """
    print(f"🔨 {desc}...")
    
    # 1. Remember where we started
    original_dir = os.getcwd()
    
    # 2. Find the folder containing 'dbt_project.yml'
    # This searches the current directory and one level deep
    dbt_dir = None
    if os.path.exists("dbt_project.yml"):
        dbt_dir = "."
    else:
        # Search immediate subdirectories
        for item in os.listdir("."):
            if os.path.isdir(item) and "dbt_project.yml" in os.listdir(item):
                dbt_dir = item
                break
    
    if not dbt_dir:
        print("❌ Error: Could not find 'dbt_project.yml' in current or sub directories.")
        sys.exit(1)

    try:
        # 3. Switch Context
        print(f"   📂 Switching to dbt directory: {dbt_dir}")
        os.chdir(dbt_dir)
        
        # 4. Run the Command
        subprocess.check_call(command, shell=True)
        print(f"✅ {desc} Complete!\n")
        
    except subprocess.CalledProcessError:
        print(f"❌ Error during: {desc}")
        sys.exit(1)
    finally:
        # 5. Always switch back, even if it failed
        os.chdir(original_dir)
def main():
    print("🚀 Starting Project Build...\n")

    # 1. Install Python Dependencies
    run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing Python Dependencies")

    # 2. Start Docker Containers
    run_command("docker compose up -d", "Starting Docker Infrastructure")

    # 3. Wait for Postgres (Simple sleep, or you could loop check)
    print("⏳ Waiting 10s for Database to initialize...")
    time.sleep(10)

    # 4. Initialize Data (dbt)
    # Note: We run run-operation first to ensure tables exist, then seed, then run
    run_dbt_command("dbt seed", "Seeding Static Data")
    run_dbt_command("dbt run", "Building dbt Models")

    print("🎉 Build Complete! You can now run 'python run.py'")

if __name__ == "__main__":
    main()