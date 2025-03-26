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
from .spell import Spell

if TYPE_CHECKING:
    from hearthstone import cardxml

    from ..player import Player


class Secret(Spell):
    spelltype = enums.SpellType.SECRET

    def dump_hidden(self):
        if self.zone == Zone.SECRET:
            data = super().dump_hidden()
            data["type"] = int(CardType.SPELL)
            data["cost"] = self.cost
            if self.card_class == CardClass.MAGE:
                data["id"] = "SECRET_MAGE"
                data["name"] = "Mage Secret"
            elif self.card_class == CardClass.HUNTER:
                data["id"] = "SECRET_HUNTER"
                data["name"] = "Hunter Secret"
            elif self.card_class == CardClass.PALADIN:
                data["id"] = "SECRET_PALADIN"
                data["name"] = "Paladin Secret"
            elif self.card_class == CardClass.ROGUE:
                data["id"] = "SECRET_ROGUE"
                data["name"] = "Rogue Secret"
            data["rarity"] = int(Rarity.INVALID)
            data["description"] = "Be careful! This card's effect will trigger in a special situation..."
            data["spelltype"] = int(self.spelltype)
            data["classes"] = [int(card_class) for card_class in self.classes]
            return data
        return super().dump_hidden()

    @property
    def events(self):
        ret = super().events
        if self.zone == Zone.SECRET and not self.exhausted:
            ret += self.data.scripts.secret
        return ret

    @property
    def exhausted(self):
        return self.zone == Zone.SECRET and self.controller.current_player

    @property
    def zone_position(self):
        if self.zone == Zone.SECRET:
            return self.controller.secrets.index(self) + 1
        return super().zone_position

    def _set_zone(self, value):
        if value == Zone.PLAY:
            # Move secrets to the SECRET Zone when played
            value = Zone.SECRET
        if self.zone == Zone.SECRET:
            self.controller.secrets.remove(self)
        if value == Zone.SECRET:
            self.controller.secrets.append(self)
        super()._set_zone(value)

    def is_summonable(self):
        # secrets are all unique
        if self.controller.secrets.contains(self.id):
            return False
        if len(self.controller.secrets) >= self.game.MAX_SECRETS_ON_PLAY:
            return False
        return super().is_summonable()

