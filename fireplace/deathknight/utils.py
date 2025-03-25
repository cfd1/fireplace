"""
Utility functions for Death Knight implementation.
"""

from typing import Optional

from hearthstone.enums import CardClass
from ..card import Card
from .runes import RuneCost


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