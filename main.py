import subprocess
import sys
import os
from threading import Thread

def run_script(script_name):
    """Run a Python script in a separate process"""
    try:
        print(f"[MAIN] Starting {script_name}...")
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[MAIN] Error running {script_name}: {e}")
    except KeyboardInterrupt:
        print(f"[MAIN] Stopped {script_name}")

def main():
    # Create necessary folders
    os.makedirs("./images", exist_ok=True)
    os.makedirs("./responses", exist_ok=True)

    # List of scripts to run
    scripts = [
        "OCR.py",    # Your OpenAI text analysis script
        "OpenAI.py"    # Your OCR image processing script
    ]

    # Create threads for each script
    threads = []
    for script in scripts:
        thread = Thread(target=run_script, args=(script,))
        thread.daemon = True  # This allows the program to exit even if threads are running
        threads.append(thread)

    # Start all threads
    print("[MAIN] Starting all monitoring scripts...")
    for thread in threads:
        thread.start()

    try:
        # Keep the main program running
        while True:
            for thread in threads:
                thread.join(0.1)  # Check thread status every 0.1 seconds
    except KeyboardInterrupt:
        print("\n[MAIN] Stopping all monitors...")
        sys.exit(0)

if __name__ == "__main__":
    main()