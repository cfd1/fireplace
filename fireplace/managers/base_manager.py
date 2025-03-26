class Manager(object):
    tag_map = {}

    def __init__(self, obj):
        self.obj = obj
        self.observers = []

    def __getitem__(self, tag):
        if self.tag_map.get(tag):
            return getattr(self.obj, self.tag_map[tag], 0)
        raise KeyError

    def __setitem__(self, tag, value):
        setattr(self.obj, self.tag_map[tag], value)

    def __iter__(self):
        for k in self.tag_map:
            if self.tag_map[k]:
                yield k

    def get(self, k, default=None):
        return self[k] if k in self.tag_map else default

    def items(self):
        for k, v in self.tag_map.items():
            if v is not None:
                yield k, self[k]

    def register(self, observer):
        self.observers.append(observer)

    def update(self, tags):
        for k, v in tags.items():
            if self.tag_map.get(k) is not None:
                self[k] = v 