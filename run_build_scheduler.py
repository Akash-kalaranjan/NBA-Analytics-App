"""
Automated scheduler runner for build_dataset.py
Logs output to a file for monitoring
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
MODELS_DIR = PROJECT_DIR / "Models"
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Create timestamped log file
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = LOG_DIR / f"build_run_{timestamp}.log"

print(f"Starting automated build at {timestamp}")
print(f"Log file: {log_file}")

try:
    with open(log_file, "w") as f:
        f.write(f"Build started at {timestamp}\n")
        f.write(f"Project dir: {PROJECT_DIR}\n")
        f.write("="*60 + "\n\n")
        
        # Run build_dataset.py
        result = subprocess.run(
            [sys.executable, str(MODELS_DIR / "build_dataset.py")],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        # Write output
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\n\nSTDERR:\n")
        f.write(result.stderr)
        f.write("\n\n")
        f.write("="*60 + "\n")
        f.write(f"Build finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Exit code: {result.returncode}\n")
        
        if result.returncode == 0:
            f.write("Build completed successfully\n")
            print("Build completed successfully")
        else:
            f.write("Build failed\n")
            print("Build failed")
            sys.exit(1)

except subprocess.TimeoutExpired:
    with open(log_file, "a") as f:
        f.write(f"\nBuild timed out after 1 hour\n")
    print("Build timed out")
    sys.exit(1)
    
except Exception as e:
    with open(log_file, "a") as f:
        f.write(f"\nError: {e}\n")
    print(f"Error: {e}")
    sys.exit(1)
