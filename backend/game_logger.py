import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class GameLogger:
    def __init__(self, log_dir: str = "game_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def log_game(self, game_data: Dict[str, Any]):
        """Journaliser une partie complète"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        game_id = game_data.get("game_id", "unknown")

        # Log JSON
        