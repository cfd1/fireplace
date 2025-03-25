from tests.utils import prepare_game
from hearthstone.enums import CardType, GameTag
from hearthstone import cardxml


def test_location_type():
    """Test that location cards are recognized correctly"""
    # Create a mock location card
    from fireplace.card import Location
    from fireplace.cards import db
    
    # Create a CardXML object
    mock_data = cardxml.CardXML("TEST_LOCATION")
    # Set tags directly instead of trying to set attributes
    mock_data.tags[GameTag.CARDTYPE] = int(CardType.LOCATION)
    mock_data.tags[GameTag.COST] = 3
    
    # Add required attributes for card initialization
    mock_data.entourage = []
    mock_data.requirements = {}
    mock_data.choose_cards = []
    
    # Create a mock scripts class
    class MockScripts:
        location_action_cooldown = 2
        events = []
        play = []
        deathrattle = []
        update = []
        progress_total = 0
        
        # Add required classes for card
        class Hand:
            events = []
            update = []
            
        class Deck:
            events = []
            update = []
    
    mock_data.scripts = MockScripts
    
    # Register it temporarily
    db["TEST_LOCATION"] = mock_data
    
    # Test creating the card
    from fireplace.card import Card
    card = Card("TEST_LOCATION")
    
    # Check that it's recognized as a Location
    assert isinstance(card, Location)
    assert card.type == CardType.LOCATION
    assert card.location_action_cooldown == 2
    
    # Clean up
    del db["TEST_LOCATION"]


def test_location_cooldown():
    """Test location card cooldown mechanics"""
    # This is a minimal test that doesn't require an actual card
    from fireplace.card import Location
    from fireplace.cards import db
    
    # Create a CardXML object
    mock_data = cardxml.CardXML("TEST_LOCATION_COOLDOWN")
    # Set tags directly instead of trying to set attributes
    mock_data.tags[GameTag.CARDTYPE] = int(CardType.LOCATION)
    mock_data.tags[GameTag.COST] = 3
    
    # Add required attributes for card initialization
    mock_data.entourage = []
    mock_data.requirements = {}
    mock_data.choose_cards = []
    
    # Create a mock scripts class
    class MockScripts:
        location_action_cooldown = 2
        events = []
        play = []
        deathrattle = []
        update = []
        progress_total = 0
        
        # Add methods required for the Card class
        def cost_mod(self, card):
            return 0
            
        # Add required classes for card
        class Hand:
            events = []
            update = []
            
        class Deck:
            events = []
            update = []
    
    mock_data.scripts = MockScripts
    
    # Register it temporarily
    db["TEST_LOCATION_COOLDOWN"] = mock_data
    
    # Set up a game
    game = prepare_game()
    
    # Give the location card to player1
    from fireplace.card import Card
    game.player1.give("TEST_LOCATION_COOLDOWN")
    
    # Play the location
    game.player1.hand[0].play()
    
    # Check initial state - now reference the field card directly
    field_location = game.player1.field[0]
    assert field_location.cooldown == 0
    assert field_location.is_usable() is True
    
    # Activate the location
    field_location.activate()
    
    # Check cooldown is applied
    assert field_location.cooldown == 2
    assert field_location.is_usable() is False
    
    # Clean up
    del db["TEST_LOCATION_COOLDOWN"] 