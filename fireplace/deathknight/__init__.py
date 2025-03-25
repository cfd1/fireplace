"""
Death Knight class and Rune system implementation.
Introduced in March of the Lich King expansion (Patch 25.0.0).
"""

from enum import Enum
from typing import List, Dict, Optional, Set, TYPE_CHECKING

from hearthstone.enums import CardClass, GameTag

from ..player import Player
from ..actions import TargetedAction, ActionArg, IntArg, LazyValue
from ..card import Card


class RuneType(Enum):
    """Rune types for Death Knight cards."""
    BLOOD = 1
    FROST = 2
    UNHOLY = 3


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


class GainCorpse(TargetedAction):
    """
    Generate corpses for the player.
    """
    TARGET = ActionArg()
    AMOUNT = IntArg()

    def do(self, source, target, amount=1):
        if not isinstance(target, DeathKnightPlayer):
            return False

        target.generate_corpse(amount)
        return True


class SpendCorpse(TargetedAction):
    """
    Spend corpses from the player.
    If successful and action is provided, perform that action.
    """
    TARGET = ActionArg()
    AMOUNT = IntArg()
    ACTION = ActionArg()

    def _get_amount(self, source, target):
        """Get the amount of corpses to spend."""
        if self._args[1] is not None:
            return self.evaluate_target(source, self._args[1])
        return 1

    def get_target_args(self, source, target):
        amount = self._get_amount(source, target)
        action = self.eval(self._args[2], source)
        return target, amount, action

    def do(self, source, target, amount, action=None):
        if not isinstance(target, DeathKnightPlayer):
            return False

        if target.spend_corpse(amount):
            if action:
                source.game.queue_actions(source, [action])
            return True
        
        return False


def get_card_rune_cost(card: Card) -> Optional[RuneCost]:
    """
    Extract the rune cost from a card's data.
    
    Returns a RuneCost object if the card has a rune cost,
    or None if it doesn't.
    """
    # This would normally use GameTag enum values to get rune costs
    # Since those don't exist yet, we'll parse it from the card's requirements
    # This is a stub implementation that would need to be updated 
    # when the actual GameTags for runes are defined.
    
    # Example implementation - in reality this would read from card tags
    if card.card_class != CardClass.DEATHKNIGHT:
        return None
    
    # This is just a placeholder - in actual implementation we'd 
    # read these values from the card data
    return RuneCost(0, 0, 0, 0) 

__all__ = [
    "RuneType",
    "RuneCost", 
    "RuneSet",
    "DeathKnightPlayer",
    "GainCorpse",
    "SpendCorpse",
    "get_card_rune_cost",
] 