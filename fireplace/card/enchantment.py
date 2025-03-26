from hearthstone.enums import Zone
from .base import BaseCard
from ..entity import boolean_property, int_property

class Enchantment(BaseCard):
    atk = int_property("atk")
    cost = int_property("cost")
    has_deathrattle = boolean_property("has_deathrattle")
    incoming_damage_multiplier = int_property("incoming_damage_multiplier")
    max_health = int_property("max_health")
    spellpower = int_property("spellpower")
    min_health = int_property("min_health")

    buffs = []
    slots = []

    def __init__(self, data):
        self.one_turn_effect = False
        self.additional_deathrattles = []
        super().__init__(data)

    @property
    def events(self):
        events = super().events
        if self.owner.zone == Zone.HAND:
            events += self.data.scripts.Hand.events
        if self.owner.zone == Zone.DECK:
            events += self.data.scripts.Deck.events
        return events

    @property
    def deathrattles(self):
        if not self.has_deathrattle:
            return []
        ret = self.additional_deathrattles[:]
        deathrattle = self.get_actions("deathrattle")
        if deathrattle:
            ret.append(deathrattle)
        return ret

    def _getattr(self, attr, i):
        i += getattr(self, "_" + attr, 0)
        return getattr(self.data.scripts, attr, lambda s, x: x)(self, i)

    def _set_zone(self, zone):
        if zone == Zone.PLAY:
            self.owner.buffs.append(self)
        elif zone == Zone.REMOVEDFROMGAME:
            if self.zone == zone:
                # Can happen if a Destroy is queued after a bounce, for example
                self.logger.warning("Trying to remove %r which is already gone", self)
                return
            if hasattr(self.owner, "health"):
                old_health = self.owner.health
            self.owner.buffs.remove(self)
            if self in self.game.active_aura_buffs:
                self.game.active_aura_buffs.remove(self)
            if hasattr(self.owner, "health"):
                if self.owner.health < old_health:
                    self.owner.damage = max(
                        self.owner.damage - (old_health - self.owner.health), 0
                    )
        super()._set_zone(zone)

    def apply(self, target):
        self.log("Applying %r to %r", self, target)
        self.owner = target
        if hasattr(self.data.scripts, "apply"):
            self.data.scripts.apply(self, target)
        if hasattr(self.data.scripts, "max_health"):
            self.log("%r removes all damage from %r", self, target)
            target.damage = 0
        self.zone = Zone.PLAY

    def remove(self):
        self.zone = Zone.REMOVEDFROMGAME 