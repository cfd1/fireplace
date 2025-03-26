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


class Character(LiveEntity):
    health_attribute = "health"
    cant_attack = boolean_property("cant_attack")
    cant_be_frozen = boolean_property("cant_be_frozen")
    cant_be_targeted_by_opponents = boolean_property("cant_be_targeted_by_opponents")
    cant_be_targeted_by_abilities = boolean_property("cant_be_targeted_by_abilities")
    cant_be_targeted_by_hero_powers = boolean_property(
        "cant_be_targeted_by_hero_powers"
    )

    heavily_armored = boolean_property("heavily_armored")
    min_health = int_property("min_health")
    rush = boolean_property("rush")
    taunt = boolean_property("taunt")
    ignore_taunt = boolean_property("ignore_taunt")
    cannot_attack_heroes = boolean_property("cannot_attack_heroes")
    unlimited_attacks = boolean_property("unlimited_attacks")
    stealthed = boolean_property("stealthed")

    def __init__(self, data):
        self._frozen = False
        self.attack_target = None
        self.num_attacks = 0
        self.race = Race.INVALID
        super().__init__(data)

    def dump(self):
        data = super().dump()
        data["heavily_armored"] = self.heavily_armored
        data["taunt"] = self.taunt
        data["poisonous"] = self.poisonous
        data["stealthed"] = self.stealthed
        data["frozen"] = self.frozen
        data["race"] = int(self.race)
        data["can_attack"] = self.can_attack()
        return data

    @property
    def events(self):
        ret = super().events
        if self.heavily_armored:
            ret += rules.HEAVILY_ARMORED
        return ret

    @property
    def attackable(self):
        return not self.immune

    @property
    def attacking(self):
        return self.attack_target is not None

    @property
    def attack_targets(self):
        targets = self.controller.opponent.characters
        if self.cannot_attack_heroes:
            targets = self.controller.opponent.field
        if self.rush and not self.turns_in_play:
            targets = self.controller.opponent.field
        targets = targets.filter(dormant=False)

        taunts = []
        if not self.ignore_taunt:
            taunts = targets.filter(taunt=True).filter(attackable=True)

        return (taunts or targets).filter(attackable=True)

    @property
    def frozen(self):
        if self.cant_be_frozen:
            self._frozen = False
        return self._frozen

    @frozen.setter
    def frozen(self, value):
        if self.cant_be_frozen:
            value = False
        self._frozen = value

    def can_attack(self, target=None):
        if self.controller.choice:
            return False
        if not self.zone == Zone.PLAY:
            return False
        if self.cant_attack:
            return False
        if not self.controller.current_player:
            return False
        if not self.atk:
            return False
        if self.exhausted:
            return False
        if self.frozen:
            return False
        if not self.attack_targets:
            return False
        if target is not None and target not in self.attack_targets:
            return False

        return True

    @property
    def max_attacks(self):
        if self.mega_windfury:
            return 4
        if self.windfury:
            return 2
        return 1

    @property
    def exhausted(self):
        if self.unlimited_attacks:
            return False
        if self.num_attacks >= self.max_attacks:
            return True
        return False

    @property
    def races(self):
        if self.race == Race.ALL:
            return [
                Race.ELEMENTAL,
                Race.MECHANICAL,
                Race.DEMON,
                Race.DRAGON,
                Race.MURLOC,
                Race.BEAST,
                Race.PIRATE,
                Race.TOTEM,
            ]
        return [self.race]

    @property
    def should_exit_combat(self):
        if self.attacking:
            if self.dead or self.zone != Zone.PLAY:
                return True
        return False

    def attack(self, target):
        if not self.can_attack(target):
            raise InvalidAction("%r can't attack %r." % (self, target))
        self.game.attack(self, target)

    @property
    def health(self):
        return self.max_health - self.damage

    @property
    def targets(self):
        if self.zone == Zone.PLAY:
            return self.attack_targets
        return super().targets

    def set_current_health(self, amount):
        return self.game.cheat_action(self, [actions.SetCurrentHealth(self, amount)])
