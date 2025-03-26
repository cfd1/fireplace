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


class SideQuest(Spell):
    spelltype = enums.SpellType.SIDEQUEST

    @property
    def zone_position(self):
        if self.zone == Zone.SECRET:
            return self.controller.secrets.index(self) + 1
        return super().zone_position

    def dump_hidden(self):
        if self.zone == Zone.SECRET:
            return self.dump()
        return super().dump_hidden()

    def is_summonable(self):
        if self.controller.secrets.contains(self.id):
            return False
        if len(self.controller.secrets) >= self.game.MAX_SECRETS_ON_PLAY:
            return False
        return super().is_summonable()

    def _set_zone(self, value):
        if value == Zone.PLAY:
            value = Zone.SECRET
        if self.zone == Zone.SECRET:
            self.controller.secrets.remove(self)
        if value == Zone.SECRET:
            self.controller.secrets.append(self)
        super()._set_zone(value)

    @property
    def events(self):
        ret = super().events
        if self.zone == Zone.SECRET:
            ret += self.data.scripts.sidequest
        return ret

