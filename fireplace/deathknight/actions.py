"""
Death Knight specific actions implementation.
"""

from ..actions import TargetedAction, ActionArg, IntArg
from .player import DeathKnightPlayer


class GainCorpse(TargetedAction):
    """
    Generate corpses for the player.
    """
    TARGET = ActionArg()
    AMOUNT = IntArg()

    def do(self, source, target, amount=1):
        if not isinstance(target, DeathKnightPlayer):
            return False

        target.generate_corpse(amount)
        return True


class SpendCorpse(TargetedAction):
    """
    Spend corpses from the player.
    If successful and action is provided, perform that action.
    """
    TARGET = ActionArg()
    AMOUNT = IntArg()
    ACTION = ActionArg()

    def _get_amount(self, source, target):
        """Get the amount of corpses to spend."""
        if self._args[1] is not None:
            return self.evaluate(self._args[1], source)
        return 1

    def get_target_args(self, source, target):
        amount = self._get_amount(source, target)
        action = self.eval(self._args[2], source)
        return target, amount, action

    def do(self, source, target, amount, action=None):
        if not isinstance(target, DeathKnightPlayer):
            return False

        if target.spend_corpse(amount):
            if action:
                source.game.queue_actions(source, [action])
            return True
        
        return False 