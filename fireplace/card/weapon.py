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
from .live_entity import LiveEntity

if TYPE_CHECKING:
    from hearthstone import cardxml

    from ..player import Player


class Weapon(rules.WeaponRules, LiveEntity):
    health_attribute = "durability"

    def __init__(self, *args):
        super().__init__(*args)
        self.damage = 0

    def dump(self):
        data = super().dump()
        data["max_durability"] = self.max_durability
        return data

    @property
    def durability(self):
        return self.max_durability - self.damage

    @property
    def max_durability(self):
        ret = self._max_durability
        ret += self._getattr("max_health", 0)
        return max(0, ret)

    @max_durability.setter
    def max_durability(self, value):
        self._max_durability = value

    @property
    def exhausted(self):
        return self.zone == Zone.PLAY and not self.controller.current_player

    def _set_zone(self, zone):
        if zone == Zone.PLAY:
            if self.controller.weapon:
                self.log("Destroying old weapon %r", self.controller.weapon)
                self.controller.weapon.destroy()
            self.controller.weapon = self
        elif self.zone == Zone.PLAY:
            self.controller.weapon = None
        super()._set_zone(zone)

