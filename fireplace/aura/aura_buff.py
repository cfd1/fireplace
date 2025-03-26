from fireplace.logging import log
from fireplace.managers import CardManager


class AuraBuff:
    def __init__(self, source, entity):
        self.source = source
        self.entity = entity
        self.tags = CardManager(self)

    def __repr__(self):
        return "<AuraBuff %r -> %r>" % (self.source, self.entity)

    def update_tags(self, tags):
        self.tags.update(tags)
        self.tick = self.source.game.tick

    def remove(self):
        log.info("Destroying %r", self)
        self.entity.slots.remove(self)
        self.source.game.active_aura_buffs.remove(self)

    def _getattr(self, attr, i):
        value = getattr(self, attr, 0)
        if callable(value):
            return value(self.entity, i)
        return i + value 