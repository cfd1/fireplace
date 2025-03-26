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
from .base import BaseCard

if TYPE_CHECKING:
    from hearthstone import cardxml

    from ..player import Player


class PlayableCard(BaseCard, Entity, TargetableByAuras):
    windfury = boolean_property("windfury")
    mega_windfury = boolean_property("mega_windfury")
    has_choose_one = boolean_property("has_choose_one")
    playable_zone = Zone.HAND
    lifesteal = boolean_property("lifesteal")
    keep_buff = boolean_property("keep_buff")
    echo = boolean_property("echo")
    has_overkill = boolean_property("has_overkill")
    has_discover = boolean_property("has_discover")
    libram = boolean_property("libram")

    def __init__(self, data):
        self.cant_play = False
        self.entourage = CardList(data.entourage)
        self.has_battlecry = False
        self.has_combo = False
        self.overload = 0
        self.rarity = Rarity.INVALID
        self.choose_cards = CardList()
        self.morphed = None
        self.turn_drawn = -1
        self.turn_played = -1
        self.cast_on_friendly_characters = False
        self.cast_on_friendly_minions = False
        self.play_left_most = False
        self.play_right_most = False
        self.custom_card = False
        super().__init__(data)

    def dump(self):
        data = super().dump()
        data["rarity"] = int(self.rarity)
        data["cost"] = self.cost
        data["powered_up"] = self.powered_up
        data["targets"] = [card.entity_id for card in self.targets]
        data["choose_cards"] = [card.dump() for card in self.choose_cards]
        data["windfury"] = self.windfury
        data["lifesteal"] = self.lifesteal
        data["events"] = bool(self._events)
        data["must_choose_one"] = self.must_choose_one
        return data

    @property
    def events(self):
        if self.zone == Zone.HAND:
            return self.data.scripts.Hand.events
        if self.zone == Zone.DECK:
            return self.data.scripts.Deck.events
        return self.base_events + list(self._events)

    @property
    def cost(self):
        ret = 0
        if self.zone == Zone.HAND and self.game.turn > 0:
            mod = self.data.scripts.cost_mod
            if mod is not None:
                r = mod.evaluate(self)
                # evaluate() can return None if it's an Evaluator (Crush)
                if r:
                    ret += r
        ret = self._getattr("cost", ret)
        return max(0, ret)

    @cost.setter
    def cost(self, value):
        self._cost = value

    @property
    def must_choose_one(self):
        """
        Returns True if the card has active choices
        """
        if self.controller.choose_both and self.has_choose_one:
            return False
        return bool(self.choose_cards)

    @property
    def powered_up(self):
        """
        Returns True whether the card is "powered up".
        """
        if not self.data.scripts.powered_up:
            return False
        for script in self.data.scripts.powered_up:
            if not script.check(self):
                return False
        return True

    @property
    def entities(self):
        return chain([self], self.buffs)

    @property
    def drawn_this_turn(self):
        return self.turn_drawn == self.game.turn

    @property
    def played_this_turn(self):
        return self.turn_played == self.game.turn

    @property
    def play_outcast(self):
        return self.play_left_most or self.play_right_most

    @property
    def zone_position(self):
        """
        Returns the card's position (1-indexed) in its zone, or 0 if not available.
        """
        if self.zone == Zone.HAND:
            return self.controller.hand.index(self) + 1
        return 0

    def _set_zone(self, zone):
        old_zone = self.zone
        super()._set_zone(zone)
        if old_zone == Zone.PLAY and zone not in (Zone.GRAVEYARD, Zone.SETASIDE):
            if not self.keep_buff:
                self.clear_buffs()
            if self.id == self.controller.cthun.id:
                self.controller.copy_cthun_buff(self)

        if self.zone == Zone.HAND:
            # Create the "Choose One" subcards
            del self.choose_cards[:]
            for id in self.data.choose_cards:
                card = self.controller.card(id, source=self, parent=self)
                self.choose_cards.append(card)

    def destroy(self):
        return self.game.cheat_action(self, [actions.Destroy(self), actions.Deaths()])

    def discard(self):
        return self.game.cheat_action(self, [actions.Discard(self)])

    def draw(self):
        return self.game.cheat_action(self, [actions.Draw(self.controller, self)])

    def heal(self, target, amount):
        return self.game.cheat_action(self, [actions.Heal(target, amount)])

    def is_playable(self):
        if self.controller.choice:
            return False

        if not self.controller.current_player:
            return False

        if self.parent_card:
            zone = self.parent_card.zone
            playable_zone = self.parent_card.playable_zone
            if not self.controller.can_pay_cost(self.parent_card):
                return False
        else:
            zone = self.zone
            playable_zone = self.playable_zone
            if not self.controller.can_pay_cost(self):
                return False

        if zone != playable_zone:
            return False

        if self.must_choose_one:
            for card in self.choose_cards:
                if card.is_playable():
                    return True
            return False

        if PlayReq.REQ_TARGET_TO_PLAY in self.requirements:
            if not self.play_targets:
                return False

        if PlayReq.REQ_NUM_MINION_SLOTS in self.requirements:
            if (
                self.requirements[PlayReq.REQ_NUM_MINION_SLOTS]
                > self.controller.minion_slots
            ):
                return False

        if PlayReq.REQ_BOARD_NOT_COMPLETELY_FULL in self.requirements:
            if (
                self.controller.minion_slots == 0
                and self.controller.opponent.minion_slots == 0
            ):
                return False

        min_enemy_minions = self.requirements.get(PlayReq.REQ_MINIMUM_ENEMY_MINIONS, 0)
        if len(self.controller.opponent.field) < min_enemy_minions:
            return False

        min_total_minions = self.requirements.get(PlayReq.REQ_MINIMUM_TOTAL_MINIONS, 0)
        if len(self.controller.game.board) < min_total_minions:
            return False

        if PlayReq.REQ_ENTIRE_ENTOURAGE_NOT_IN_PLAY in self.requirements:
            if not [
                id for id in self.entourage if not self.controller.field.contains(id)
            ]:
                return False

        if PlayReq.REQ_WEAPON_EQUIPPED in self.requirements:
            if not self.controller.weapon:
                return False

        if PlayReq.REQ_FRIENDLY_MINION_DIED_THIS_GAME in self.requirements:
            if not self.controller.graveyard.filter(type=CardType.MINION):
                return False

        if PlayReq.REQ_SECRET_ZONE_CAP_FOR_NON_SECRET in self.requirements:
            if len(self.controller.secrets) >= self.game.MAX_SECRETS_ON_PLAY:
                return False

        if PlayReq.REQ_MINION_SLOT_OR_MANA_CRYSTAL_SLOT in self.requirements:
            if (
                len(self.controller.game.board) >= self.game.MAX_MINIONS_ON_FIELD
                and self.controller.max_mana >= self.controller.max_resources
            ):
                return False

        if PlayReq.REQ_MUST_PLAY_OTHER_CARD_FIRST in self.requirements:
            if not any(getattr(e, "played_this_turn", False) for e in self.game):
                return False

        if PlayReq.REQ_HAND_NOT_FULL in self.requirements:
            if len(self.controller.hand) >= self.controller.max_hand_size:
                return False

        if PlayReq.REQ_CANNOT_PLAY_THIS in self.requirements:
            return False

        if PlayReq.REQ_FRIENDLY_MINIONS_OF_RACE_DIED_THIS_GAME in self.requirements:
            race = self.requirements.get(
                PlayReq.REQ_FRIENDLY_MINIONS_OF_RACE_DIED_THIS_GAME, 0
            )
            if not self.controller.graveyard.filter(type=CardType.MINION, race=race):
                return False

        if PlayReq.REQ_FRIENDLY_MINION_OF_RACE_DIED_THIS_TURN in self.requirements:
            race = self.requirements.get(
                PlayReq.REQ_FRIENDLY_MINIONS_OF_RACE_DIED_THIS_GAME, 0
            )
            if not self.controller.graveyard.filter(killed_this_turn=True, race=race):
                return False

        if PlayReq.REQ_FRIENDLY_MINION_OF_RACE_IN_HAND in self.requirements:
            race = self.requirements.get(PlayReq.REQ_FRIENDLY_MINION_OF_RACE_IN_HAND, 0)
            if not self.controller.hand.filter(races=race):
                return False

        if PlayReq.REQ_FRIENDLY_DEATHRATTLE_MINION_DIED_THIS_GAME in self.requirements:
            if not self.controller.graveyard.filter(has_deathrattle=True):
                return False

        return self.is_summonable()

    def play(self, target=None, index=None, choose=None):
        """
        Queue a Play action on the card.
        """
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
        if not self.is_playable():
            raise InvalidAction("%r isn't playable." % (self))
        if card.requires_target():
            if not target:
                raise InvalidAction("%r requires a target to play." % (self))
            elif target not in self.play_targets:
                raise InvalidAction("%r is not a valid target for %r." % (target, self))
            if self.controller.all_targets_random:
                new_target = random.choice(self.play_targets)
                self.logger.info(
                    "Retargeting %r from %r to %r", self, target, new_target
                )
                target = new_target
        elif target:
            self.logger.warning(
                "%r does not require a target, ignoring target %r", self, target
            )
            target = None
        self.game.play_card(self, target, index, choose)
        return self

    def is_summonable(self) -> bool:
        """
        Return whether the card can be summoned.
        Do not confuse with is_playable()
        """
        return True

    def morph(self, into):
        """
        Morph the card into another card
        """
        return self.game.cheat_action(self, [actions.Morph(self, into)])

    def shuffle_into_deck(self):
        """
        Shuffle the card into the controller's deck
        """
        return self.game.cheat_action(self, [actions.Shuffle(self.controller, self)])

    def put_on_top(self):
        """
        Put the card into the controller's deck top
        """
        return self.game.cheat_action(self, [actions.PutOnTop(self.controller, self)])

    def battlecry_requires_target(self):
        """
        True if the play action of the card requires a target
        """
        if self.has_combo and self.controller.combo:
            if PlayReq.REQ_TARGET_FOR_COMBO in self.requirements:
                return True

        for req in TARGETING_PREREQUISITES:
            if req in self.requirements:
                return True
        return False

    def requires_target(self):
        """
        True if the card currently requires a target
        """
        if self.has_combo and PlayReq.REQ_TARGET_FOR_COMBO in self.requirements:
            if self.controller.combo:
                return bool(self.play_targets)
        if PlayReq.REQ_TARGET_IF_AVAILABLE in self.requirements:
            return bool(self.play_targets)
        if PlayReq.REQ_TARGET_IF_AVAILABLE_AND_DRAGON_IN_HAND in self.requirements:
            if self.controller.hand.filter(races=Race.DRAGON):
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_MINIMUM_FRIENDLY_MINIONS
        )
        if req is not None:
            if len(self.controller.field) >= req:
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_MINIMUM_FRIENDLY_SECRETS
        )
        if req is not None:
            if len(self.controller.secrets) >= req:
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_HERO_ATTACKED_THIS_TURN
        )
        if req is not None:
            if self.controller.hero.num_attacks > 0:
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABE_AND_ELEMENTAL_PLAYED_LAST_TURN
        )
        if req is not None:
            if self.controller.elemental_played_last_turn:
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_NO_3_COST_CARD_IN_DECK
        )
        if req is not None:
            if len(self.controller.deck.filter(cost=3)) == 0:
                return bool(self.play_targets)
        req = self.requirements.get(PlayReq.REQ_TARGET_IF_AVAILABLE_AND_HERO_HAS_ATTACK)
        if req is not None:
            if self.controller.hero.atk >= 0:
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_MINIMUM_SPELLS_PLAYED_THIS_TURN
        )
        if req is not None:
            if (
                sum(
                    getattr(e, "played_this_turn", False)
                    and getattr(e, "type", None) == CardType.SPELL
                    for e in self.game
                )
                >= req
            ):
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_HAS_OVERLOADED_MANA
        )
        if req is not None:
            if self.controller.overloaded > 0 or self.controller.overload_locked > 0:
                return bool(self.play_targets)
        req = self.requirements.get(PlayReq.REQ_TARGET_IF_AVAILABLE_AND_DRAWN_THIS_TURN)
        if req is not None:
            if self.drawn_this_turn:
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_NOT_DRAWN_THIS_TURN
        )
        if req is not None:
            if not self.drawn_this_turn:
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_ONLY_EVEN_COST_CARD_IN_DECK
        )
        if req is not None:
            if all(card.cost % 2 == 0 for card in self.controller.deck):
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_ONLY_ODD_COST_CARD_IN_DECK
        )
        if req is not None:
            if all(card.cost % 2 == 1 for card in self.controller.deck):
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_COST_5_OR_MORE_SPELL_IN_HAND
        )
        if req is not None:
            if self.controller.hand.filter(cost=range(5, 100)):
                return bool(self.play_targets)
        req = self.requirements.get(
            PlayReq.REQ_TARGET_IF_AVAILABLE_AND_MIN_MANA_CRYSTAL
        )
        if req is not None:
            if self.controller.max_mana >= req:
                return bool(self.play_targets)
        req = self.requirements.get(PlayReq.REQ_TARGET_IF_AVAILABLE_AND_FRIENDLY_LACKEY)
        if req is not None:
            if self.controller.field.filter(mark_of_evil=True):
                return bool(self.play_targets)
        req = self.requirements.get(PlayReq.REQ_STEADY_SHOT)
        if req is not None:
            if self.steady_shot_can_target:
                return bool(self.play_targets)
        req = self.requirements.get(PlayReq)
        return PlayReq.REQ_TARGET_TO_PLAY in self.requirements

    @property
    def play_targets(self):
        return [card for card in self.game.characters if is_valid_target(self, card)]

    @property
    def targets(self):
        return self.play_targets

