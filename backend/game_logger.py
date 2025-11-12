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
        json_file = self.log_dir / f"game_{timestamp}_{game_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)

        # Log CSV pour stats
        self._update_stats_csv(game_data)

    def _update_stats_csv(self, game_data: Dict[str, Any]):
        """Mettre à jour le fichier de statistique CSV"""
        csv_file = self.log_dir / "game_stats.csv"

        headers = [
            "timestamp", "game_id", "winner", "move_count", "model_x", "model_o", "duration_seconds"
        ]

        row = {
            "timestamp": datetime.now().isoformat(),
            "game_id": game_data.get("game_id", ""),
            "winner": game_data.get("winner", "draw"),
            "move_count": game_data.get("move_count", 0),
            "model_x": game_data.get("model_x", "unknown"),
            "model_o": game_data.get("model_o", "unknown"),
            "duration_seconds": game_data.get("duration_seconds", 0)
        }

        file_exists = csv_file.exists()

        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    def get_game_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer l'historique des parties"""
        games = []
        json_files = sorted(self.log_dir.glob("game_*.json"), reverse=True)

        for file_path in json_files[:limit]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                    games.append(game_data)
            except Exception as e:
                print(f"Erreur lecture {file_path}: {e}")
        return games