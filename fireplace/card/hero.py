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

if TYPE_CHECKING:
    from hearthstone import cardxml

    from ..player import Player

class Hero(Character):
    galakrond_hero_card = boolean_property("galakrond_hero_card")

    def __init__(self, data):
        self.armor = 0
        self.power: HeroPower = None
        super().__init__(data)

    def dump(self):
        data = super().dump()
        data["armor"] = self.armor
        return data

    @property
    def entities(self):
        yield self
        if self.zone == Zone.PLAY:
            if self.power:
                yield self.power
            if self.controller.weapon:
                yield self.controller.weapon
        yield from self.buffs

    @property
    def windfury(self):
        ret = super().windfury
        if self.controller.weapon:
            # NOTE: As of 9786, Windfury is retained even when the weapon is exhausted.
            return self.controller.weapon.windfury or ret
        return ret

    @property
    def lifesteal(self):
        ret = super().lifesteal
        if self.controller.weapon and not self.controller.weapon.exhausted:
            return self.controller.weapon.lifesteal or ret
        return ret

    @property
    def poisonous(self):
        ret = super().poisonous
        if self.controller.weapon and not self.controller.weapon.exhausted:
            return self.controller.weapon.poisonous or ret
        return ret

    @property
    def has_overkill(self):
        ret = super().has_overkill
        if self.controller.weapon and not self.controller.weapon.exhausted:
            return self.controller.weapon.has_overkill or ret
        return ret

    def _getattr(self, attr, i):
        ret = super()._getattr(attr, i)
        if attr == "atk":
            if self.controller.weapon and not self.controller.weapon.exhausted:
                ret += self.controller.weapon.atk
        return ret

    def _set_zone(self, value):
        super()._set_zone(value)
        if value == Zone.PLAY:
            old_hero = self.controller.hero
            self.controller.hero = self
            if self.data.hero_power:
                self.controller.summon(self.data.hero_power)
            if old_hero:
                old_hero.zone = Zone.GRAVEYARD
        elif value == Zone.GRAVEYARD:
            if self.power:
                self.power.zone = Zone.GRAVEYARD
            if self.controller.hero is self:
                self.controller.playstate = PlayState.LOSING

    def _hit(self, amount):
        amount = super()._hit(amount)
        if self.armor:
            reduced_damage = min(amount, self.armor)
            self.log("%r loses %r armor instead of damage", self, reduced_damage)
            self.damage -= reduced_damage
            self.armor -= reduced_damage
        return amount

    def play(self, target=None, index=None, choose=None):
        armor = self.armor

        # Copy hero buff
        for buff in self.controller.hero.buffs:
            # Recreate the buff stack
            new_buff = self.controller.card(buff.id)
            new_buff.source = buff.source
            attributes = [
                "atk",
                "max_health",
                "_xatk",
                "_xhealth",
                "_xcost",
                "store_card",
            ]
            for attribute in attributes:
                if hasattr(buff, attribute):
                    setattr(new_buff, attribute, getattr(buff, attribute))
            new_buff.apply(self)
            if buff in self.game.active_aura_buffs:
                new_buff.tick = buff.tick
                self.game.active_aura_buffs.append(new_buff)

        self.damage = self.controller.hero.damage
        self.armor = self.controller.hero.armor
        super().play(target, index, choose)
        if armor:
            self.game.cheat_action(self, [actions.GainArmor(self, armor)])
