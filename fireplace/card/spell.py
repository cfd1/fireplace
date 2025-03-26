from hearthstone.enums import CardType, Zone, CardClass, Rarity
from .base import PlayableCard
from ..entity import boolean_property
from .. import enums, cards


class Spell(PlayableCard):
    spelltype = enums.SpellType.INVALID
    twinspell = boolean_property("twinspell")

    def __init__(self, data):
        self.immune_to_spellpower = False
        self.receives_double_spelldamage_bonus = False
        super().__init__(data)

    @property
    def twinspell_copy(self):
        if self._twinspell_copy:
            return cards.db.dbf[self._twinspell_copy]
        return None

    @twinspell_copy.setter
    def twinspell_copy(self, value):
        self._twinspell_copy = value

    def dump(self):
        data = super().dump()
        data["spelltype"] = int(self.spelltype)
        return data

    def get_damage(self, amount, target):
        amount = super().get_damage(amount, target)
        if not self.immune_to_spellpower:
            amount = self.controller.get_spell_damage(amount)
        if self.receives_double_spelldamage_bonus:
            amount = self.controller.get_spell_damage(amount)
        return amount

    def get_heal(self, amount, target):
        if not self.immune_to_spellpower:
            amount = self.controller.get_spell_heal(amount)
        return amount

    def _set_zone(self, zone):
        if zone == Zone.PLAY:
            zone = Zone.GRAVEYARD
        super()._set_zone(zone)

class Secret(Spell):
    spelltype = enums.SpellType.SECRET

    def dump_hidden(self):
        if self.zone == Zone.SECRET:
            data = super().dump_hidden()
            data["type"] = int(CardType.SPELL)
            data["cost"] = self.cost
            if self.card_class == CardClass.MAGE:
                data["id"] = "SECRET_MAGE"
                data["name"] = "法师奥秘"
            elif self.card_class == CardClass.HUNTER:
                data["id"] = "SECRET_HUNTER"
                data["name"] = "猎人奥秘"
            elif self.card_class == CardClass.PALADIN:
                data["id"] = "SECRET_PALADIN"
                data["name"] = "圣骑士奥秘"
            elif self.card_class == CardClass.ROGUE:
                data["id"] = "SECRET_ROGUE"
                data["name"] = "盗贼奥秘"
            data["rarity"] = int(Rarity.INVALID)
            data["description"] = "小心了！这张卡牌的效果在某个特殊情况下便会触发..."
            data["spelltype"] = int(self.spelltype)
            data["classes"] = [int(card_class) for card_class in self.classes]
            return data
        return super().dump_hidden()

    @property
    def events(self):
        ret = super().events
        if self.zone == Zone.SECRET and not self.exhausted:
            ret += self.data.scripts.secret
        return ret

    @property
    def exhausted(self):
        return self.zone == Zone.SECRET and self.controller.current_player

    @property
    def zone_position(self):
        if self.zone == Zone.SECRET:
            return self.controller.secrets.index(self) + 1
        return super().zone_position

    def _set_zone(self, zone):
        if zone == Zone.PLAY:
            # Move secrets to the SECRET Zone when played
            zone = Zone.SECRET
        if self.zone == Zone.SECRET:
            self.controller.secrets.remove(self)
        if zone == Zone.SECRET:
            self.controller.secrets.append(self)
        super()._set_zone(zone)

    def is_summonable(self):
        # secrets are all unique
        if self.controller.secrets.contains(self.id):
            return False
        if len(self.controller.secrets) >= self.game.MAX_SECRETS_ON_PLAY:
            return False
        return super().is_summonable()

class Quest(Spell):
    spelltype = enums.SpellType.QUEST

    def dump_hidden(self):
        if self.zone == Zone.SECRET:
            return self.dump()
        return super().dump_hidden()

    def is_summonable(self):
        if len(self.controller.secrets) > 0 and self.controller.secrets[0].data.quest:
            return False
        if len(self.controller.secrets) >= self.game.MAX_SECRETS_ON_PLAY:
            return False
        return super().is_summonable()

    def _set_zone(self, zone):
        if zone == Zone.PLAY:
            zone = Zone.SECRET
        if self.zone == Zone.SECRET:
            self.controller.secrets.remove(self)
        if zone == Zone.SECRET:
            self.controller.secrets.insert(0, self)
        super()._set_zone(zone)

    @property
    def events(self):
        ret = super().events
        if self.zone == Zone.SECRET:
            ret += self.data.scripts.quest
        return ret

class SideQuest(Spell):
    spelltype = enums.SpellType.SIDEQUEST

    @property
    def zone_position(self):
        if self.zone == Zone.SECRET:
            return self.controller.secrets.index(self) + 1
        return super().zone_position

    def dump_hidden(self):
        if self.zone == Zone.SECRET:
            return self.dump()
        return super().dump_hidden()

    def is_summonable(self):
        if self.controller.secrets.contains(self.id):
            return False
        if len(self.controller.secrets) >= self.game.MAX_SECRETS_ON_PLAY:
            return False
        return super().is_summonable()

    def _set_zone(self, zone):
        if zone == Zone.PLAY:
            zone = Zone.SECRET
        if self.zone == Zone.SECRET:
            self.controller.secrets.remove(self)
        if zone == Zone.SECRET:
            self.controller.secrets.append(self)
        super()._set_zone(zone)

    @property
    def events(self):
        ret = super().events
        if self.zone == Zone.SECRET:
            ret += self.data.scripts.sidequest
        return ret 