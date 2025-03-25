#!/usr/bin/env python
import sys; sys.path.append("..")
from utils import prepare_game, PlayAndDeathrattle
from hearthstone.enums import CardClass, CardType, GameTag
from fireplace.deathknight import DeathKnightPlayer, RuneSet
from fireplace.utils import random_draft


def test_death_knight_hero_powers():
    """Test that Death Knight hero powers and corpse mechanics work correctly"""
    # Create a Death Knight player directly
    dk_player = DeathKnightPlayer(
        name="Death Knight",
        deck=["VAN_CS1_042"],  # Just a basic card as we don't need specific cards
        hero="DK_HERO_01",  # Sire Denathrius
        runes=RuneSet(blood=3, frost=0, unholy=0)
    )
    
    # Initial state
    assert dk_player.corpses == 0
    
    # Test corpse generation
    dk_player.generate_corpse(1)
    assert dk_player.corpses == 1
    
    # Test corpse spending
    result = dk_player.spend_corpse(1)
    assert result is True
    assert dk_player.corpses == 0
    
    # Test corpse spending failure
    result = dk_player.spend_corpse(1)
    assert result is False
    assert dk_player.corpses == 0


def test_deathknight_player():
    """Test that DeathKnightPlayer extensions work properly"""
    # Create a DeathKnightPlayer
    player = DeathKnightPlayer(
        name="Death Knight",
        deck=random_draft(CardClass.DEATHKNIGHT),
        hero="DK_HERO_01",  # Sire Denathrius
        runes=RuneSet(blood=2, frost=1, unholy=0)
    )
    
    # Check runes are set properly
    assert player.runes.blood == 2
    assert player.runes.frost == 1
    assert player.runes.unholy == 0
    assert player.runes.total == 3
    
    # Check corpse mechanics
    assert player.corpses == 0
    assert player.corpses_spent_this_game == 0
    
    # Generate corpses
    player.generate_corpse(3)
    assert player.corpses == 3
    assert player.tags[GameTag.CORPSES] == 3
    
    # Spend corpses
    result = player.spend_corpse(2)
    assert result is True
    assert player.corpses == 1
    assert player.corpses_spent_this_game == 2
    
    # Try to spend more than available
    result = player.spend_corpse(2)
    assert result is False
    assert player.corpses == 1  # Unchanged
    assert player.corpses_spent_this_game == 2  # Unchanged 