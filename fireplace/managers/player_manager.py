from hearthstone.enums import GameTag

from fireplace import enums
from .base_manager import Manager


class PlayerManager(Manager):
    tag_map = {
        GameTag.CANT_DRAW: "cant_draw",
        GameTag.CARDTYPE: "type",
        GameTag.COMBO_ACTIVE: "combo",
        GameTag.CONTROLLER: "controller",
        GameTag.CURRENT_PLAYER: "current_player",
        GameTag.CURRENT_SPELLPOWER: "spellpower",
        GameTag.CURRENT_HEROPOWER_DAMAGE_BONUS: "heropower_damage",
        GameTag.EMBRACE_THE_SHADOW: "healing_as_damage",
        GameTag.FATIGUE: "fatigue_counter",
        GameTag.FIRST_PLAYER: "first_player",
        GameTag.HEALING_DOUBLE: "healing_double",
        GameTag.HERO_ENTITY: "hero",
        GameTag.INVOKE_COUNTER: "invoke_counter",
        GameTag.LAST_CARD_PLAYED: "last_card_played",
        GameTag.MAXHANDSIZE: "max_hand_size",
        GameTag.MAXRESOURCES: "max_resources",
        GameTag.NUM_CARDS_DRAWN_THIS_TURN: "cards_drawn_this_turn",
        GameTag.NUM_CARDS_PLAYED_THIS_TURN: "cards_played_this_turn",
        GameTag.NUM_HERO_POWER_DAMAGE_THIS_GAME: "hero_power_damage_this_game",
        GameTag.AMOUNT_HEALED_THIS_GAME: "healed_this_game",
        GameTag.NUM_MINIONS_PLAYED_THIS_TURN: "minions_played_this_turn",
        GameTag.NUM_MINIONS_PLAYER_KILLED_THIS_TURN: "minions_killed_this_turn",
        GameTag.NUM_TIMES_HERO_POWER_USED_THIS_GAME: "times_hero_power_used_this_game",
        GameTag.OVERLOAD_LOCKED: "overload_locked",
        GameTag.OVERLOAD_OWED: "overloaded",
        GameTag.OVERLOAD_THIS_GAME: "overloaded_this_game",
        GameTag.PLAYSTATE: "playstate",
        GameTag.RESOURCES: "max_mana",
        GameTag.RESOURCES_USED: "used_mana",
        GameTag.SPELLPOWER_DOUBLE: "spellpower_double",
        GameTag.STARTHANDSIZE: "start_hand_size",
        GameTag.HERO_POWER_DOUBLE: "hero_power_double",
        GameTag.TEMP_RESOURCES: "temp_mana",
        GameTag.TIMEOUT: "timeout",
        GameTag.TURN_START: "turn_start",
        enums.CANT_OVERLOAD: "cant_overload",
        enums.ELEMENTAL_PLAYED_LAST_TURN: "elemental_played_last_turn",
    } 