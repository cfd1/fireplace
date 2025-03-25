"""
Rune system implementation for Death Knight class.
"""

from ..enums import RuneType


class RuneCost(object):
    """
    Represents the rune cost of a Death Knight card.
    
    A card can require one or more runes of specific types,
    or it can be flexible in which rune types are used.
    """
    def __init__(self, blood: int = 0, frost: int = 0, unholy: int = 0, any: int = 0):
        self.blood = blood
        self.frost = frost
        self.unholy = unholy
        self.any = any
    
    @property
    def total(self) -> int:
        """Return the total number of runes required."""
        return self.blood + self.frost + self.unholy + self.any
    
    def __str__(self) -> str:
        parts = []
        if self.blood:
            parts.append(f"{self.blood} Blood")
        if self.frost:
            parts.append(f"{self.frost} Frost")
        if self.unholy:
            parts.append(f"{self.unholy} Unholy")
        if self.any:
            parts.append(f"{self.any} Any")
        
        return ", ".join(parts)


class RuneSet(object):
    """
    Represents a set of runes available for deck building.
    
    Death Knight decks can include up to 3 runes in total,
    which can be distributed across the three rune types.
    """
    def __init__(self, blood: int = 0, frost: int = 0, unholy: int = 0):
        self.blood = blood
        self.frost = frost
        self.unholy = unholy
    
    @property
    def total(self) -> int:
        """Return the total number of runes in the set."""
        return self.blood + self.frost + self.unholy
    
    def can_satisfy(self, cost: RuneCost) -> bool:
        """Check if this rune set can satisfy the given rune cost."""
        # First check if we have enough of each specific type
        if self.blood < cost.blood or self.frost < cost.frost or self.unholy < cost.unholy:
            return False
        
        # Then check if we have enough runes left for the "any" cost
        remaining_blood = self.blood - cost.blood
        remaining_frost = self.frost - cost.frost
        remaining_unholy = self.unholy - cost.unholy
        
        return remaining_blood + remaining_frost + remaining_unholy >= cost.any
    
    def __str__(self) -> str:
        parts = []
        if self.blood:
            parts.append(f"{self.blood} Blood")
        if self.frost:
            parts.append(f"{self.frost} Frost")
        if self.unholy:
            parts.append(f"{self.unholy} Unholy")
        
        return ", ".join(parts) 