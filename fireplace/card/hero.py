from hearthstone.enums import Zone, PlayState
from .base import Character
from ..entity import boolean_property


class Hero(Character):
    galakrond_hero_card = boolean_property("galakrond_hero_card")

    def __init__(self, data):
        self.hero_power = None
        self.hero_power_activations_this_turn = 0
        self.hero_power_activations_this_game = 0
        self.hero_power_damage_this_turn = 0
        self.hero_power_heal_this_turn = 0
        self.hero_power_damage_this_game = 0
        self.hero_power_heal_this_game = 0
        self.hero_power_damage_dealt_this_turn = 0
        self.hero_power_heal_received_this_turn = 0
        self.hero_power_damage_dealt_this_game = 0
        self.hero_power_heal_received_this_game = 0
        self.hero_power_activations_this_turn = 0
        self.hero_power_activations_this_game = 0
        super().__init__(data)

    def dump(self):
        data = super().dump()
        data["hero_power"] = self.hero_power.dump() if self.hero_power else None
        return data

    @property
    def entities(self):
        ret = super().entities
        if self.hero_power:
            ret.append(self.hero_power)
        return ret

    @property
    def windfury(self):
        return self.atk > 1

    @property
    def lifesteal(self):
        return self.atk > 0

    @property
    def poisonous(self):
        return self.atk > 0

    @property
    def has_overkill(self):
        return self.atk > 0

    def _getattr(self, attr, i):
        if attr == "atk":
            return self.atk
        return super()._getattr(attr, i)

    def _set_zone(self, zone):
        if zone == Zone.GRAVEYARD:
            if self.hero_power:
                self.hero_power.zone = Zone.GRAVEYARD
            if self.controller.hero is self:
                self.controller.playstate = PlayState.LOSING
        super()._set_zone(zone)

    def _hit(self, amount):
        amount = super()._hit(amount)
        if self.health <= 0:
            self.controller.playstate = PlayState.LOSING
        return amount

    def play(self, target=None, index=None, choose=None):
        if self.controller.hero is self:
            return self
        return super().play(target, index, choose) 