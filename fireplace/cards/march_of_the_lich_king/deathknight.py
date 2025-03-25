"""
Implementation of Death Knight hero cards and hero powers.
From March of the Lich King expansion (Patch 25.0.0).
"""

from ..utils import *
from ...deathknight import GainCorpse, SpendCorpse, RuneType


##
# Hero Powers

class DK_HERO_01bp:
    """Blood Strike
    Deal 1 damage. Gain a Corpse."""
    requirements = {PlayReq.REQ_TARGET_TO_PLAY: 0}
    activate = Hit(TARGET, 1), GainCorpse(CONTROLLER, 1)


class DK_HERO_02bp:
    """Frost Strike
    Deal 2 damage. Freeze the target."""
    requirements = {PlayReq.REQ_TARGET_TO_PLAY: 0}
    activate = Hit(TARGET, 2), Freeze(TARGET)


class DK_HERO_03bp:
    """Unholy Strike
    Summon a 2/2 Ghoul."""
    activate = Summon(CONTROLLER, "DK_HERO_03bt")


class DK_HERO_03bt:
    """Ghoul
    A 2/2 Ghoul minion summoned by Unholy Strike."""
    pass


##
# Death Knight Heroes

class DK_HERO_01:
    """Sire Denathrius
    Battlecry: Equip a 4/2 Remornia. Choose Blood Runes."""
    runes = {RuneType.BLOOD: 3}
    hero_power = "DK_HERO_01bp"
    play = Summon(CONTROLLER, "DK_REMORNIA")


class DK_REMORNIA:
    """Remornia, Living Blade
    A 4/2 weapon equipped by Sire Denathrius."""
    pass


class DK_HERO_02:
    """Lich King
    Battlecry: Freeze all enemy minions. Choose Frost Runes."""
    runes = {RuneType.FROST: 3}
    hero_power = "DK_HERO_02bp"
    play = Freeze(ENEMY_MINIONS)


class DK_HERO_03:
    """Undead Arthas
    Battlecry: Summon three 2/2 Ghouls. Choose Unholy Runes."""
    runes = {RuneType.UNHOLY: 3}
    hero_power = "DK_HERO_03bp"
    play = Summon(CONTROLLER, "DK_HERO_03bt") * 3 