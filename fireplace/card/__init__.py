from .base import BaseCard, PlayableCard, LiveEntity, Character
from .hero import Hero
from .minion import Minion
from .spell import Spell, Secret, Quest, SideQuest
from .enchantment import Enchantment
from .weapon import Weapon
from .hero_power import HeroPower
from .location import Location
from .. import cards
from hearthstone.enums import CardType

__all__ = [
    "BaseCard",
    "PlayableCard",
    "LiveEntity",
    "Character",
    "Hero",
    "Minion",
    "Spell",
    "Secret",
    "Quest",
    "SideQuest",
    "Enchantment",
    "Weapon",
    "HeroPower",
    "Location",
]


def Card(card_id):
    data = cards.db[card_id]
    subclass = {
        CardType.HERO: Hero,
        CardType.MINION: Minion,
        CardType.SPELL: Spell,
        CardType.ENCHANTMENT: Enchantment,
        CardType.WEAPON: Weapon,
        CardType.HERO_POWER: HeroPower,
        CardType.LOCATION: Location,
    }[data.type]
    if subclass is Spell:
        if data.secret:
            subclass = Secret
        elif data.quest:
            subclass = Quest
        elif data.sidequest:
            subclass = SideQuest

    return subclass(data)
