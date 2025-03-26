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


class LiveEntity(PlayableCard, Entity):
    has_deathrattle = boolean_property("has_deathrattle")
    secret_deathrattle = int_property("secret_deathrattle")
    atk = int_property("atk")
    cant_be_damaged = boolean_property("cant_be_damaged")
    immune_while_attacking = slot_property("immune_while_attacking")
    incoming_damage_multiplier = int_property("incoming_damage_multiplier")
    max_health = int_property("max_health")
    poisonous = boolean_property("poisonous")

    def __init__(self, data):
        super().__init__(data)
        self._to_be_destroyed = False
        self.damage = 0
        self.forgetful = False
        self.predamage = 0
        self.turns_in_play = 0
        self.turn_killed = -1
        self.damaged_this_turn = 0
        self.healed_this_turn = 0
        self.additional_deathrattles = []

    def dump(self):
        data = super().dump()
        data["has_deathrattle"] = self.has_deathrattle
        data["atk"] = self.atk
        data["max_health"] = self.max_health
        data["damage"] = self.damage
        data["immune"] = self.immune
        return data

    def _set_zone(self, zone):
        if zone == Zone.GRAVEYARD and self.zone == Zone.PLAY:
            self.turn_killed = self.game.turn
        super()._set_zone(zone)
        # See issue #283 (Malorne, Anub'arak)
        self._to_be_destroyed = False

    @property
    def immune(self):
        if self.immune_while_attacking and self.attacking:
            return True
        return self.cant_be_damaged

    @property
    def damaged(self):
        return bool(self.damage)

    @property
    def deathrattles(self):
        ret = []
        if not self.has_deathrattle:
            return ret
        ret = self.additional_deathrattles[:]
        deathrattle = self.get_actions("deathrattle")
        if deathrattle:
            ret.append(deathrattle)
        if self.secret_deathrattle:
            secret_deathrattles = self.get_actions("secret_deathrattles")
            ret.append((secret_deathrattles[self.secret_deathrattle - 1],))
        return ret

    @property
    def dead(self):
        return (
            self.zone == Zone.GRAVEYARD
            or self.to_be_destroyed
            or getattr(self, self.health_attribute) <= 0
        )

    @property
    def delayed_destruction(self):
        return self.zone == Zone.PLAY

    @property
    def to_be_destroyed(self):
        return self._to_be_destroyed

    @to_be_destroyed.setter
    def to_be_destroyed(self, value):
        self._to_be_destroyed = value

    @property
    def killed_this_turn(self):
        return self.turn_killed == self.game.turn

    def _hit(self, amount):
        self.damage += amount
        return amount

    def hit(self, amount):
        return self.game.cheat_action(self, [actions.Hit(self, amount)])

