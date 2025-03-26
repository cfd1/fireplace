from . import LazyValue, Selector


class Switch:
    """
    Switch statement on the ID of an entity
    Perform actions as described in the map
    """

    def __init__(self, selector, switch_map):
        self.selector = selector
        self.switch_map = switch_map

    @property
    def default(self):
        return self.switch_map.get(None, ())

    def evaluate(self, source):
        entities = self.selector.eval(source.game, source)
        if not entities:
            return self.default
        assert len(entities) == 1, "Switch() on more than 1 entity: %r" % (entities)
        card_id = entities[0].id if hasattr(entities[0], "id") else entities[0]
        if card_id not in self.switch_map:
            return self.default
        return self.switch_map[card_id]

    def trigger(self, source):
        action = self.evaluate(source)
        if action:
            action.trigger(source)
