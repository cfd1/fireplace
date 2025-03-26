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
from .playable import PlayableCard

if TYPE_CHECKING:
    from hearthstone import cardxml

    from ..player import Player


class Spell(PlayableCard):
    spelltype = enums.SpellType.INVALID
    twinspell = boolean_property("twinspell")

    def __init__(self, data):
        self.immune_to_spellpower = False
        self.receives_double_spelldamage_bonus = False
        super().__init__(data)

    @property
    def twinspell_copy(self):
        if self._twinspell_copy:
            return cards.db.dbf[self._twinspell_copy]
        return None

    @twinspell_copy.setter
    def twinspell_copy(self, value):
        self._twinspell_copy = value

    def dump(self):
        data = super().dump()
        data["spelltype"] = int(self.spelltype)
        return data

    def get_damage(self, amount, target):
        amount = super().get_damage(amount, target)
        if not self.immune_to_spellpower:
            amount = self.controller.get_spell_damage(amount)
        if self.receives_double_spelldamage_bonus:
            amount = self.controller.get_spell_damage(amount)
        return amount

    def get_heal(self, amount, target):
        if not self.immune_to_spellpower:
            amount = self.controller.get_spell_heal(amount)
        return amount

    def _set_zone(self, value):
        if value == Zone.PLAY:
            value = Zone.GRAVEYARD
        super()._set_zone(value)

