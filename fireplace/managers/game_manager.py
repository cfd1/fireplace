from hearthstone.enums import GameTag
from .base_manager import Manager


class GameManager(Manager):
    map = {
        GameTag.CARDTYPE: "type",
        GameTag.NEXT_STEP: "next_step",
        GameTag.NUM_MINIONS_KILLED_THIS_TURN: "minions_killed_this_turn",
        GameTag.PROPOSED_ATTACKER: "proposed_attacker",
        GameTag.PROPOSED_DEFENDER: "proposed_defender",
        GameTag.STATE: "state",
        GameTag.STEP: "step",
        GameTag.TURN: "turn",
        GameTag.ZONE: "zone",
    }

    def __init__(self, obj):
        super().__init__(obj)
        self.counter = 1
        obj.entity_id = self.counter

    def action_start(self, type, source, index, target):
        for observer in self.observers:
            observer.action_start(type, source, index, target)

    def action_end(self, type, source):
        for observer in self.observers:
            observer.action_end(type, source)

    def new_entity(self, entity):
        self.counter += 1
        entity.entity_id = self.counter
        for observer in self.observers:
            observer.new_entity(entity)

    def start_game(self):
        for observer in self.observers:
            observer.start_game()

    def step(self, step, next_step=None):
        for observer in self.observers:
            observer.game_step(step, next_step)
        self.obj.step = step
        if next_step is not None:
            self.obj.next_step = next_step

    def turn(self, player):
        for observer in self.observers:
            observer.turn(player)

    def game_action(self, action, source, *args):
        for observer in self.observers:
            observer.game_action(action, source, *args)

    def targeted_action(self, action, source, target, *args):
        for observer in self.observers:
            observer.targeted_action(action, source, target, *args) 