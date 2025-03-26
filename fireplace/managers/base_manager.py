class Manager(object):
    map = {}

    def __init__(self, obj):
        self.obj = obj
        self.observers = []

    def __getitem__(self, tag):
        if self.map.get(tag):
            return getattr(self.obj, self.map[tag], 0)
        raise KeyError

    def __setitem__(self, tag, value):
        setattr(self.obj, self.map[tag], value)

    def __iter__(self):
        for k in self.map:
            if self.map[k]:
                yield k

    def get(self, k, default=None):
        return self[k] if k in self.map else default

    def items(self):
        for k, v in self.map.items():
            if v is not None:
                yield k, self[k]

    def register(self, observer):
        self.observers.append(observer)

    def update(self, tags):
        for k, v in tags.items():
            if self.map.get(k) is not None:
                self[k] = v 