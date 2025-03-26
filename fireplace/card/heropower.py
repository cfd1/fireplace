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


class HeroPower(PlayableCard):
    additional_activations = int_property("additional_activations")
    heropower_disabled = int_property("heropower_disabled")
    passive_hero_power = boolean_property("passive_hero_power")
    playable_zone = Zone.PLAY
    steady_shot_can_target = boolean_property("steady_shot_can_target")

    def __init__(self, data):
        self.activations_this_turn = 0
        self.additional_activations_this_turn = 0
        self._upgraded_hero_power = None
        super().__init__(data)

    def dump(self):
        data = super().dump()
        data["is_usable"] = self.is_usable()
        return data

    @property
    def exhausted(self):
        if self.heropower_disabled:
            return True
        if self.additional_activations == -1:
            return False
        return self.activations_this_turn >= (
            1 + self.additional_activations + self.additional_activations_this_turn
        )

    @property
    def events(self):
        if self.heropower_disabled:
            return []
        return super().events

    @property
    def update_scripts(self):
        if not self.heropower_disabled:
            yield from super().update_scripts

    @property
    def upgraded_hero_power(self):
        if self._upgraded_hero_power:
            return cards.db.dbf[self._upgraded_hero_power]
        return None

    @upgraded_hero_power.setter
    def upgraded_hero_power(self, value):
        self._upgraded_hero_power = value

    def _set_zone(self, value):
        if value == Zone.PLAY:
            if self.controller.hero.power:
                self.controller.hero.power.destroy()
            self.controller.hero.power = self
            # Create the "Choose One" subcards
            del self.choose_cards[:]
            for id in self.data.choose_cards:
                card = self.controller.card(id, source=self, parent=self)
                self.choose_cards.append(card)

        super()._set_zone(value)

    def activate(self, target, choose):
        return self.game.queue_actions(
            self.controller, [actions.Activate(self, target, choose)]
        )

    def get_damage(self, amount, target):
        amount = super().get_damage(amount, target)
        return self.controller.get_heropower_damage(amount)

    def get_heal(self, amount, target):
        amount = super().get_heal(amount, target)
        return self.controller.get_heropower_heal(amount)

    def use(self, target=None, choose=None):
        if choose:
            if self.must_choose_one:
                if choose in self.choose_cards:
                    card = choose
                else:
                    choose = card = self.choose_cards.filter(id=choose)[0]
                self.log("%r: choosing %r", self, choose)
            else:
                raise InvalidAction(
                    "%r cannot be played with choice %r" % (self, choose)
                )
        else:
            if self.must_choose_one:
                raise InvalidAction(
                    "%r requires a choice (one of %r)" % (self, self.choose_cards)
                )
            card = self

        if not self.is_usable():
            raise InvalidAction("%r can't be used." % (self))

        self.log("%s uses hero power %r on %r", self.controller, card, target)

        if card.requires_target():
            if not target:
                raise InvalidAction("%r requires a target." % (self))
            elif target not in self.play_targets:
                raise InvalidAction("%r is not a valid target for %r." % (target, self))
            if self.controller.all_targets_random:
                new_target = random.choice(self.play_targets)
                self.logger.info(
                    "Retargeting %r from %r to %r", self, target, new_target
                )
                target = new_target
            self.target = target
        elif target:
            self.logger.warning(
                "%r does not require a target, ignoring target %r", self, target
            )

        ret = self.activate(target, choose)

        self.controller.times_hero_power_used_this_game += 1
        self.target = None

        return ret

    def is_usable(self):
        if self.exhausted:
            return False
        if self.passive_hero_power:
            return False
        return super().is_playable()
