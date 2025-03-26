class Refresh:
    """
    Refresh a buff or a set of tags on an entity
    """

    def __init__(self, selector, tags=None, buff=None, priority=50):
        self.selector = selector
        self.tags = tags
        self.buff = buff
        self.priority = priority

    def trigger(self, source):
        entities = self.selector.eval(source.game, source)
        for entity in entities:
            if self.buff:
                entity.refresh_buff(source, self.buff)
            else:
                tags = {}
                for tag, value in self.tags.items():
                    if not isinstance(value, int) and not callable(value):
                        value = value.evaluate(source)
                    tags[tag] = value

                entity.refresh_tags(source, tags)

    def __repr__(self):
        return "Refresh(%r, %r, %r)" % (self.selector, self.tags or {}, self.buff or "") 