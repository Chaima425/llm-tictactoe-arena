import uuid
from typing import List

class GameEngine:
    def __init__(self):
        self.grid_size = 10
        self.win_length = 5

    def create_new_game(self) -> dict:
        """Créer une nouvelle partie"""
        grid = [[" " for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        return {
            "grid": grid,
            "current_player": "X",
            "game_id": str(uuid.uuid4()),
            "winner": None,
            "move_count": 0
        }
    
    def is_valid_move(self, grid: List[List[str]], row: int, col: int) -> bool:
        """Vérifier si un coup est valide"""
        return (0 <= row < self.grid_size and
                0 <= col < self.grid_size and
                grid[row][col] == " ")
    
    def make_move(self, grid: List[List[str]], row: int, col: int, player: str) -> List[List[str]]:
        """Jouer un coup"""
        new_grid = [row[:] for row in grid]
        new_grid[row][col] = player
        return new_grid
    
    def check_winner(self, grid: List[List[str]], player: str) -> bool:
        """Vérifier si un joueur a gagné"""
        # 4 directions : horizontale, verticale et les 2 diagonales
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        # On parcours la grille sur chaque row et col
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if grid[row][col] == player:
                    for dx, dy in directions:
                        count = 1
                        for step in range(1, self.win_length):
                            nrow, ncol = row + dx * step, col + dy * step
                            if (0 <= nrow < self.grid_size and
                                0 <= ncol < self.grid_size and
                                grid[nrow][ncol] == player):
                                count += 1
                            else:
                                break
                        if count >= self.win_length:
                            return True
        return False
    
    def is_grid_full(self, grid: List[List[str]]) -> bool:
        """Vérifier si la grille est remplie"""
        return all(cell != " " for row in grid for cell in row)
    
    def _select_strategic_move(self, empty_cells: list, reason: str) -> dict:
        """Choisir un coup stratégique parmi les cases vides"""
        if not empty_cells:
            return {"row": 0, "col": 0, "raw_response": reason, "error": "no_cells"}
        
        # Priorité aux cases centrales
        center_cells = [(4,4), (4,5), (5,4), (5,5), (3,3), (3,6), (6,3), (6,6)]
        for cell in center_cells:
            if cell in empty_cells:
                return {"row": cell[0], "col": cell[1], "raw_response": f"strategic_center: {reason}"}
        
        # Sinon au hasard
        import random
        cell = random.choice(empty_cells)
        return {"row": cell[0], "col": cell[1], "raw_response": f"random_fallback: {reason}"}