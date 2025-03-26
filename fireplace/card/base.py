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


if TYPE_CHECKING:
    from hearthstone import cardxml

    from ..player import Player



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
    def zone(self, value):
        self._set_zone(value)

    def _set_zone(self, value):
        # TODO
        # Keep Buff: Deck -> Hand, Hand -> Play, Deck -> Play
        # Remove Buff: Other case
        self.old_zone = self.zone

        if self.old_zone == value:
            self.logger.warning(
                "%r attempted a same-zone move in %r", self, self.old_zone
            )
            return

        if self.old_zone:
            self.logger.debug("%r moves from %r to %r", self, self.old_zone, value)

        caches = {
            Zone.HAND: self.controller.hand,
            Zone.DECK: self.controller.deck,
            Zone.GRAVEYARD: self.controller.graveyard,
            Zone.SETASIDE: self.game.setaside,
        }
        if caches.get(self.old_zone) is not None:
            caches[self.old_zone].remove(self)
        if caches.get(value) is not None:
            if hasattr(self, "_summon_index") and self._summon_index is not None:
                caches[value].insert(self._summon_index, self)
            else:
                caches[value].append(self)
        self._zone = value

        if value == Zone.PLAY or value == Zone.SECRET:
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
