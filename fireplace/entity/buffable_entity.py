from fireplace.entity.base_entity import BaseEntity


class BuffableEntity(BaseEntity):
    def __init__(self):
        super().__init__()
        self.buffs = []
        self.slots = []

    def _getattr(self, attr, i):
        i += getattr(self, "_" + attr, 0)
        for buff in self.buffs:
            i = buff._getattr(attr, i)
        for slot in self.slots:
            i = slot._getattr(attr, i)
        if self.ignore_scripts:
            return i
        return getattr(self.data.scripts, attr, lambda s, x: x)(self, i)

    def clear_buffs(self):
        if self.buffs:
            self.log("Clearing buffs from %r", self)
            for buff in self.buffs[:]:
                buff.remove() 