from itertools import chain
import random
import re
from typing import TYPE_CHECKING
from hearthstone.enums import (
    CardClass,
    CardType,
    GameTag,
    MultiClassGroup,
    Race,
    Rarity,
    Zone,
)

from .. import actions, rules
from ..aura import TargetableByAuras
from ..dsl.lazynum import LazyNum
from ..entity import BaseEntity, Entity, boolean_property, int_property, slot_property
from ..enums import PlayReq
from ..exceptions import InvalidAction
from ..managers import CardManager
from ..targeting import TARGETING_PREREQUISITES, is_valid_target
from ..utils import CardList

if TYPE_CHECKING:
    from hearthstone import cardxml
    from ..player import Player

THE_COIN = "GAME_005"



class BaseCard(BaseEntity):
    Manager = CardManager
    delayed_destruction = False

    def __init__(self, data: "cardxml.CardXML"):
        self.data = data
        super().__init__()
        self.requirements = data.requirements.copy()
        self.id: str = data.id
        self.controller: Player = None
        self.choose = None
        self.target = None
        self.parent_card: BaseCard = None
        self.aura = False
        self.heropower_damage = 0
        self._zone = Zone.INVALID
        self._progress: int = 0
        self.progress_total: int = data.scripts.progress_total
        self.card_class = CardClass.INVALID
        self.multi_class_group = MultiClassGroup.INVALID
        self.tags.update(data.tags)

    def dump(self):
        data = super().dump()
        data["id"] = self.id
        data["name"] = self.data.name
        data["description"] = self.description
        data["classes"] = [int(card_class) for card_class in self.classes]
        data["is_playable"] = self.is_playable()
        data["progress"] = self.progress
        data["progress_total"] = self.progress_total
        data["zone"] = int(self.zone)
        return data

    def dump_hidden(self):
        if self.zone == Zone.PLAY:
            return self.dump()
        return super().dump_hidden()

    def __str__(self):
        return self.data.name

    def __hash__(self):
        return self.id.__hash__()

    def __repr__(self):
        return "<%s (%r)>" % (self.__class__.__name__, self.__str__())

    def __eq__(self, other):
        if isinstance(other, BaseCard):
            return self.entity_id.__eq__(other.entity_id)
        elif isinstance(other, str):
            return self.id.__eq__(other)
        return super().__eq__(other)

    @property
    def is_standard(self):
        return self.data.is_standard

    @property
    def name_enUS(self):
        return self.data.strings[GameTag.CARDNAME]["enUS"]

    @property
    def description(self):
        description = self.data.description
        if "@" in description:
            hand_description, description = description.split("@", 1)
            if self.zone is Zone.HAND:
                description = hand_description
        formats = []
        format_tags = [
            GameTag.CARDTEXT_ENTITY_0,
            GameTag.CARDTEXT_ENTITY_1,
            GameTag.CARDTEXT_ENTITY_2,
            GameTag.CARDTEXT_ENTITY_3,
            GameTag.CARDTEXT_ENTITY_4,
            GameTag.CARDTEXT_ENTITY_5,
            GameTag.CARDTEXT_ENTITY_6,
            GameTag.CARDTEXT_ENTITY_7,
            GameTag.CARDTEXT_ENTITY_8,
            GameTag.CARDTEXT_ENTITY_9,
        ]
        formats = []
        for format_tag in format_tags:
            entity = self.tags[format_tag]
            if isinstance(entity, LazyNum):
                formats.append(entity.evaluate(self))
            elif isinstance(entity, dict):
                if self.data.locale in entity:
                    formats.append(entity[self.data.locale])
                else:
                    formats.append("")
            else:
                break

        description = description.format(*formats)
        # https://github.com/HearthSim/hs-bugs/issues/459
        description = description.replace("[x]", "")
        if self.type == CardType.SPELL:
            description = re.sub(
                "\\$(?P<damage>\\d+)",
                lambda match: str(
                    self.controller.get_spell_damage(int(match.group("damage")))
                ),
                description,
            )
            description = re.sub(
                "\\#(?P<heal>\\d+)",
                lambda match: str(
                    self.controller.get_spell_heal(int(match.group("heal")))
                ),
                description,
            )
        elif self.type == CardType.HERO_POWER:
            description = re.sub(
                "\\$(?P<damage>\\d+)",
                lambda match: str(
                    self.controller.get_heropower_damage(int(match.group("damage")))
                ),
                description,
            )
            description = re.sub(
                "\\#(?P<heal>\\d+)",
                lambda match: str(
                    self.controller.get_heropower_heal(int(match.group("heal")))
                ),
                description,
            )
        return description

    @property
    def game(self):
        return self.controller.game

    @property
    def zone(self):
        return self._zone

    @property
    def classes(self):
        if self.multi_class_group != MultiClassGroup.INVALID:
            return MultiClassGroup(self.multi_class_group).card_classes
        return [self.card_class]

    @zone.setter
    def zone(self, zone):
        self._set_zone(zone)

    def _set_zone(self, zone):
        # TODO
        # Keep Buff: Deck -> Hand, Hand -> Play, Deck -> Play
        # Remove Buff: Other case
        self.old_zone = self.zone

        if self.old_zone == zone:
            self.logger.warning(
                "%r attempted a same-zone move in %r", self, self.old_zone
            )
            return

        if self.old_zone:
            self.logger.debug("%r moves from %r to %r", self, self.old_zone, zone)

        caches = {
            Zone.HAND: self.controller.hand,
            Zone.DECK: self.controller.deck,
            Zone.GRAVEYARD: self.controller.graveyard,
            Zone.SETASIDE: self.game.setaside,
        }
        if caches.get(self.old_zone) is not None:
            caches[self.old_zone].remove(self)
        if caches.get(zone) is not None:
            if hasattr(self, "_summon_index") and self._summon_index is not None:
                caches[zone].insert(self._summon_index, self)
            else:
                caches[zone].append(self)
        self._zone = zone

        if zone == Zone.PLAY or zone == Zone.SECRET:
            self.play_counter = self.game.play_counter
            self.game.play_counter += 1

    def buff(self, target, buff, **kwargs):
        """
        Summon \a buff and apply it to \a target
        If keyword arguments are given, attempt to set the given
        values to the buff. Example:
        player.buff(target, health=random.randint(1, 5))
        NOTE: Any Card can buff any other Card. The controller of the
        Card that buffs the target becomes the controller of the buff.
        """
        ret = self.controller.card(buff, self)
        ret.source = self
        ret.apply(target)
        for k, v in kwargs.items():
            setattr(ret, k, v)
        return ret

    def is_playable(self) -> bool:
        """
        Return whether the card can be played.
        Do not confuse with is_summonable()
        """
        return False

    def play(self, *args):
        raise NotImplementedError

    def add_progress(self, card, amount):
        if self.data.scripts.add_progress and amount == 1:
            # Rogue quest: The Caverns Below
            return self.data.scripts.add_progress(self, card)
        self.progress += amount

    @property
    def progress(self):
        if hasattr(self, "card_name_counter"):
            return max(self.card_name_counter.values())
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value

    def clear_progress(self):
        self.progress = 0

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
            for card_id in self.data.choose_cards:
                card = self.controller.card(card_id, source=self, parent=self)
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
        self._max_durability = self.data.durability

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

