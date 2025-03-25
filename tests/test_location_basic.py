from hearthstone.enums import CardType
from fireplace.card import Card, Location

def test_card_location_type():
    """Test that the Location card type is properly registered in the Card function"""
    # Import needed for subclass mapping
    import fireplace.card
    import inspect
    
    # Get the source code of the Card function
    card_function_source = inspect.getsource(fireplace.card.Card)
    
    # Check that the mapping has an entry for Location
    assert "CardType.LOCATION: Location," in card_function_source 