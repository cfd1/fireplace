from hearthstone.enums import Zone
from .base import LiveEntity
from .. import rules

class Weapon(rules.WeaponRules, LiveEntity):
    health_attribute = "durability"

    def __init__(self, *args):
        super().__init__(*args)
        self.damage = 0
        self._max_durability = self.data.durability

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