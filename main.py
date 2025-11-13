import subprocess
import sys
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    backend_process = None
    frontend_process = None
    
    try:
        logger.info("Lancement du backend FastAPI...")
        backend_dir = Path(__file__).parent / "backend"
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api:app", "--reload", "--host", "127.0.0.1", "--port", "8000"], 
            cwd=backend_dir
        )

        time.sleep(3)
        
        logger.info("Lancement du frontend NiceGUI...")
        frontend_dir = Path(__file__).parent / "frontend"
        frontend_process = subprocess.Popen([sys.executable, "app.py"], cwd=frontend_dir)

        logger.info("Application lancée ! http://127.0.0.1:8080")
        frontend_process.wait()
        
    except KeyboardInterrupt:
        logger.info("\nArrêt...")
        for process in [backend_process, frontend_process]:
            if process:
                process.terminate()
        logger.info("Application arrêtée")

if __name__ == "__main__":
    main()