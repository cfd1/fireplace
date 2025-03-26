import uuid

from hearthstone.enums import CardType

from fireplace import logging


class BaseEntity(object):
    base_events = []
    logger = logging.log
    ignore_scripts = False
    type = CardType.INVALID

    def __init__(self):
        self.manager = self.Manager(self)
        self.play_counter = 0
        self.tags = self.manager
        self.uuid = uuid.uuid4()
        self.event_args = None

        if self.data:
            self._events = self.data.scripts.events[:]
        else:
            self._events = []

    def dump(self):
        return {
            "entity_id": self.entity_id,
            "type": int(self.type),
        }

    def dump_hidden(self):
        return {
            "entity_id": self.entity_id,
        }

    def __int__(self):
        return self.entity_id

    @property
    def is_card(self):
        """
        True if the Entity is a real card (as opposed to a Player, Game, ...)
        """
        return self.type > CardType.PLAYER

    @property
    def events(self):
        return self.base_events + list(self._events)

    @property
    def update_scripts(self):
        if self.data and not self.ignore_scripts:
            yield from self.data.scripts.update

    def log(self, message, *args):
        self.logger.info(message, *args)

    def get_actions(self, name):
        actions = getattr(self.data.scripts, name)
        if callable(actions):
            actions = actions(self)
        return actions

    def trigger_event(self, source, event, args):
        """
        Trigger an event on the Entity
        * \a source: The source of the event
        * \a event: The event being triggered
        * \a args: A list of arguments to pass to the callback
        """
        actions = []
        for action in event.actions:
            if callable(action):
                ac = action(self, *args)
                if not ac:
                    # Handle falsy returns
                    continue
                if not hasattr(ac, "__iter__"):
                    actions.append(ac)
                else:
                    actions += action(self, *args)
            else:
                actions.append(action)
        ret = source.game.trigger(self, actions, args)
        if event.once:
            self._events.remove(event)

        return ret

    def get_damage(self, amount: int, target) -> int:
        """
        Override to modify the damage dealt to a target from the given amount.
        """
        if getattr(target, "dormant", False):
            self.log("%r is dormant to %s for %i damage", target, self, amount)
            return 0
        if target.immune:
            self.log("%r is immune to %s for %i damage", target, self, amount)
            return 0
        return amount

    def get_heal(self, amount: int, target) -> int:
        return amount 