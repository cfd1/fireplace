"""
Death Knight player implementation.
"""

from typing import Optional

from ..player import Player
from .runes import RuneSet


class DeathKnightPlayer(Player):
    """
    Player subclass for Death Knight class.
    
    This class extends the base Player with Death Knight specific functionality:
    - Rune system for deck building
    - Corpse generation and tracking
    """
    
    def __init__(self, name, deck: list[str], hero: str, is_standard=True, runes: Optional[RuneSet] = None):
        super().__init__(name, deck, hero, is_standard)
        
        # Initialize Death Knight specific attributes
        self.runes = runes or RuneSet()
        self.corpses = 0
        self.corpses_spent_this_game = 0
    
    def generate_corpse(self, amount: int = 1) -> None:
        """Generate the specified amount of corpses for the player."""
        self.corpses += amount
        self.log("%s generates %i corpse(s) (total: %i)", self, amount, self.corpses)
    
    def spend_corpse(self, amount: int = 1) -> bool:
        """
        Attempt to spend the specified amount of corpses.
        
        Returns True if successful, False if there weren't enough corpses.
        """
        if self.corpses < amount:
            return False
        
        self.corpses -= amount
        self.corpses_spent_this_game += amount
        self.log("%s spends %i corpse(s) (remaining: %i)", self, amount, self.corpses)
        return True 