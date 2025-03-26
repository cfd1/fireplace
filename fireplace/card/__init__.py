import random
import re
from itertools import chain
from typing import TYPE_CHECKING

from hearthstone.enums import (
    CardClass,
    CardType,
    GameTag,
    MultiClassGroup,
    PlayState,
    Race,
    Rarity,
    Step,
    Zone,
)

from .. import actions, cards, enums, rules
from ..aura import TargetableByAuras
from ..dsl.lazynum import LazyNum
from ..entity import BaseEntity, Entity, boolean_property, int_property, slot_property
from ..enums import PlayReq
from ..exceptions import InvalidAction
from ..managers import CardManager
from ..targeting import TARGETING_PREREQUISITES, is_valid_target
from ..utils import CardList

from .character import Character
from .hero import Hero
from .minion import Minion
from .spell import Spell
from .secret import Secret
from .quest import Quest
from .sidequest import SideQuest
from .enchantment import Enchantment
from .weapon import Weapon
from .heropower import HeroPower


if TYPE_CHECKING:
    from hearthstone import cardxml

    from ..player import Player

THE_COIN = "GAME_005"


def Card(id):
    data = cards.db[id]
    subclass = {
        CardType.HERO: Hero,
        CardType.MINION: Minion,
        CardType.SPELL: Spell,
        CardType.ENCHANTMENT: Enchantment,
        CardType.WEAPON: Weapon,
        CardType.HERO_POWER: HeroPower,
    }[data.type]
    if subclass is Spell:
        if data.secret:
            subclass = Secret
        elif data.quest:
            subclass = Quest
        elif data.sidequest:
            subclass = SideQuest

    return subclass(data)
