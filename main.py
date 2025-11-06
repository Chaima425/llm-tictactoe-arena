# main.py
import subprocess
import sys
import time
import os
from pathlib import Path

if __name__ == "__main__":
    backend_process = None
    frontend_process = None
    
    try:
        # Lancer le backend
        print("Lancement du backend FastAPI...")
        backend_dir = Path(__file__).parent / "backend"
        # Le PYTHONPATH est utile si le backend devait importer des modules du parent
        env = os.environ.copy()
        env["PYTHONPATH"] = str(backend_dir.parent) + os.pathsep + env.get("PYTHONPATH", "")
        
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"], 
            cwd=backend_dir, 
            env=env
        )

        print("Attente du démarrage du backend (5 secondes)...")
        time.sleep(5)

        # Lancer le frontend
        print("Lancement du frontend NiceGUI...")
        frontend_dir = Path(__file__).parent / "frontend"
        frontend_process = subprocess.Popen([sys.executable, "app.py"], cwd=frontend_dir)

        print("\n" + "="*50)
        print("Application lancée !")
        print("Interface web : http://127.0.0.1:8080")
        print("API Backend   : http://127.0.0.1:8000")
        print("Appuyez sur Ctrl+C pour arrêter l'application.")
        print("="*50 + "\n")
        
        # Attendre indéfiniment ou jusqu'à une interruption
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nArrêt des processus en cours...")
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
            print("Backend arrêté.")
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
            print("Frontend arrêté.")
        print("Application arrêtée avec succès.")
        sys.exit(0)