import os
import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path(__file__).parent / "src"))

# Redirect to the actual app
if __name__ == "__main__":
    os.system("streamlit run src/presentation/streamlit/app.py")
