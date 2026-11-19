import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from bootstrap_paths import activate

activate()

directory = os.path.abspath(os.path.dirname(__file__))

PROCESSES = [
    "IngestionProcess.py",
    "KPIProcessing.py",
    "ExcelOutput.py",
]


def run_process(script_name):
    script_path = os.path.join(directory, script_name)
    print(f"\n{'=' * 40}")
    print(f"Running {script_name}")
    print(f"{'=' * 40}\n")
    subprocess.run([sys.executable, script_path], check=True)


if __name__ == "__main__":
    for script in PROCESSES:
        run_process(script)
    print("\nDaily refresh completed successfully.")
