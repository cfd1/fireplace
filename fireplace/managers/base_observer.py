class BaseObserver:
    def action_start(self, type, source, index, target):
        pass

    def action_end(self, type, source):
        pass

    def game_step(self, step, next_step):
        pass

    def new_entity(self, entity):
        pass

    def start_game(self):
        pass

    def turn(self, player):
        pass

    def game_action(self, action, source, *args):
        pass

    def targeted_action(self, action, source, target, *args):
        pass 