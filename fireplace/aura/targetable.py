from fireplace.logging import log
from .aura_buff import AuraBuff


class TargetableByAuras:
    def refresh_buff(self, source, id):
        for buff in self.buffs:
            if buff.source is source and buff.id == id:
                buff.tick = source.game.tick
                break
        else:
            log.info("Aura from %r buffs %r with %r", source, self, id)
            buff = source.buff(self, id)
            buff.tick = source.game.tick
            source.game.active_aura_buffs.append(buff)

    def refresh_tags(self, source, tags):
        for slot in self.slots:
            if slot.source is source:
                slot.update_tags(tags)
                break
        else:
            buff = AuraBuff(source, self)
            log.info("Creating %r", buff)
            buff.update_tags(tags)
            self.slots.append(buff)
            source.game.active_aura_buffs.append(buff) 