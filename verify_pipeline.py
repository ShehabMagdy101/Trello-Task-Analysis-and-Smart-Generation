import subprocess
import sys

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
    return result.returncode

run_cmd("venv\\Scripts\\python.exe -m src.application.data_pipeline.fetcher")
run_cmd("venv\\Scripts\\python.exe -m src.application.data_pipeline.processor")
