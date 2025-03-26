def slot_property(attr, f=any):
    @property
    def func(self):
        return f(getattr(slot, attr, False) for slot in self.slots)

    return func


def boolean_property(attr):
    @property
    def func(self):
        return (
            getattr(self, "_" + attr, False)
            or (any(getattr(buff, attr, False) for buff in self.buffs))
            or (any(getattr(slot, attr, False) for slot in self.slots))
            or (getattr(self.data.scripts, attr, lambda s, x: x)(self, False))
        )

    @func.setter
    def func(self, value):
        setattr(self, "_" + attr, value)

    return func


def int_property(attr):
    @property
    def func(self):
        ret = self._getattr(attr, 0)
        return max(0, ret)

    @func.setter
    def func(self, value):
        setattr(self, "_" + attr, value)

    return func 