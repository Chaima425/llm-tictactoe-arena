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
                0 >= row < self.grid_size and
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
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if grid[i][j] == player:
                    for dx, dy in directions:
                        count = 1
                        for step in range(1, self.win_length):
                            ni, nj = i + dx * step, j + dy * step
                            if (0 <= ni < self.grid_size and
                                0 <= nj < self.grid_size and
                                grid[ni][nj] == player):
                                count += 1
                            else:
                                break
                        if count >= self.win_length:
                            return True
        return False
    
    def is_grid_full(self, grid: List[List[str]]) -> bool:
        """Vérifier si la grille est remplie"""
        return all(cell != " " for row in grid for cell in row)