from hearthstone.enums import Zone
from .base import Character
from ..entity import boolean_property, int_property
from .. import actions
from ..utils import CardList


class Minion(Character):
    charge = boolean_property("charge")
    has_inspire = boolean_property("has_inspire")
    spellpower = int_property("spellpower")
    has_magnetic = boolean_property("has_magnetic")
    mark_of_evil = boolean_property("mark_of_evil")

    silenceable_attributes = (
        "always_wins_brawls",
        "aura",
        "cant_attack",
        "cant_be_targeted_by_abilities",
        "cant_be_targeted_by_hero_powers",
        "charge",
        "divine_shield",
        "enrage",
        "forgetful",
        "frozen",
        "has_deathrattle",
        "has_inspire",
        "lifesteal",
        "poisonous",
        "stealthed",
        "taunt",
        "windfury",
        "cannot_attack_heroes",
        "rush",
        "secret_deathrattle",
        "has_overkill",
        "reborn",
    )

    def __init__(self, data):
        self.always_wins_brawls = False
        self.divine_shield = False
        self.enrage = False
        self.silenced = False
        self._summon_index = None
        self.dormant = False
        self.dormant_turns = data.scripts.dormant_turns
        self.reborn = False
        super().__init__(data)

    def dump(self):
        data = super().dump()
        data["has_inspire"] = self.has_inspire
        data["divine_shield"] = self.divine_shield
        data["silenced"] = self.silenced
        data["dormant"] = self.dormant
        data["reborn"] = self.reborn
        return data

    @property
    def ignore_scripts(self):
        return self.silenced or self.dormant

    @property
    def left_minion(self):
        assert self.zone is Zone.PLAY, self.zone
        ret = CardList()
        index = self.zone_position - 1
        left = self.controller.field[:index].filter(dormant=False)
        if left:
            ret.append(left[-1])
        return ret

    @property
    def right_minion(self):
        assert self.zone is Zone.PLAY, self.zone
        ret = CardList()
        index = self.zone_position - 1
        right = self.controller.field[index + 1 :].filter(dormant=False)
        if right:
            ret.append(right[0])
        return ret

    @property
    def adjacent_minions(self):
        return self.left_minion + self.right_minion

    @property
    def attackable(self):
        if self.stealthed:
            return False
        if self.dormant:
            return False
        return super().attackable

    @property
    def asleep(self):
        return (
            self.zone == Zone.PLAY
            and not self.turns_in_play
            and (not self.charge and not self.rush)
        )

    @property
    def events(self):
        if self.dormant:
            return self.data.scripts.dormant_events
        return super().events

    @property
    def exhausted(self):
        if self.asleep:
            return True
        return super().exhausted

    @property
    def enraged(self):
        return self.enrage and self.damage

    @property
    def update_scripts(self):
        yield from super().update_scripts
        if self.enraged:
            yield from self.data.scripts.enrage

    @property
    def zone_position(self):
        if self.zone == Zone.PLAY:
            return self.controller.field.index(self) + 1
        return super().zone_position

    def _set_zone(self, zone):
        if zone == Zone.PLAY:
            if self._summon_index is not None:
                self.controller.field.insert(self._summon_index, self)
            else:
                self.controller.field.append(self)
        elif zone == Zone.GRAVEYARD and self.zone == Zone.PLAY:
            self.controller.minions_killed_this_turn += 1

        if self.zone == Zone.PLAY:
            self.log("%r is removed from the field", self)
            self.controller.field.remove(self)
            if self.damage:
                self.damage = 0

        super()._set_zone(zone)

    def _hit(self, amount):
        if self.divine_shield:
            self.log("%r's divine shield prevents %i damage.", self, amount)
            self.game.cheat_action(self, [actions.LosesDivineShield(self)])
            return 0

        amount = super()._hit(amount)

        if self.health < self.min_health and self.min_health > 0:
            self.log("%r has HEALTH_MINIMUM of %i", self, self.min_health)
            self.damage = self.max_health - self.min_health

        return amount

    def bounce(self):
        return self.game.cheat_action(self, [actions.Bounce(self)])

    def is_summonable(self):
        summonable = super().is_summonable()
        if len(self.controller.field) >= self.game.MAX_MINIONS_ON_FIELD:
            return False
        return summonable

    def silence(self):
        return self.game.cheat_action(self, [actions.Silence(self)])

    def can_attack(self, target=None):
        if self.dormant:
            return False

        return super().can_attack(target) 