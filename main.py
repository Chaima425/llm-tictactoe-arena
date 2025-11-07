import subprocess
import sys
import time
from pathlib import Path

def main():
    backend_process = None
    frontend_process = None
    
    try:
        print("Lancement du backend FastAPI...")
        backend_dir = Path(__file__).parent / "backend"
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"], 
            cwd=backend_dir
        )

        time.sleep(3)
        
        print("Lancement du frontend NiceGUI...")
        frontend_dir = Path(__file__).parent / "frontend"
        frontend_process = subprocess.Popen([sys.executable, "app.py"], cwd=frontend_dir)

        print("Application lancée ! http://127.0.0.1:8080")
        frontend_process.wait()
        
    except KeyboardInterrupt:
        print("\nArrêt...")
        for process in [backend_process, frontend_process]:
            if process:
                process.terminate()
        print("Application arrêtée")

if __name__ == "__main__":
    main()