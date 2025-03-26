from hearthstone.enums import Zone
from .base import PlayableCard
from ..events import OWN_TURN_BEGIN
from ..actions import Reduce_Cooldown, SELF
from ..entity import boolean_property

class Location(PlayableCard):
    """
    Location cards are a new type of card that was added in Patch 16.6.0.
    They have specific functionality including action cooldown.
    """
    
    playable_zone = Zone.PLAY
    shifting_location = boolean_property("shifting_location")
    events = []  # Default empty events list

    def __init__(self, data):
        super().__init__(data)
        # Initialize instance variables specific to locations
        self._cooldown = 0
        self._turns_in_play = 0
        self._immune = False
        self._to_be_destroyed = False
        
    @property
    def location_action_cooldown(self):
        if isinstance(getattr(self.data.scripts, "location_action_cooldown", 0), int):
            return getattr(self.data.scripts, "location_action_cooldown", 0)
        
        return self._getattr("location_action_cooldown", 0)
        
    @property
    def location_action_cost(self):
        if isinstance(getattr(self.data.scripts, "location_action_cost", 0), int):
            return getattr(self.data.scripts, "location_action_cost", 0)
        else:
            return self._getattr("location_action_cost", 0)
    
    @property
    def immune(self):
        return self._immune
        
    @immune.setter
    def immune(self, value):
        self._immune = value
        
    @property
    def incoming_damage_multiplier(self):
        return 1
    
    @property
    def to_be_destroyed(self):
        return self._to_be_destroyed
        
    @to_be_destroyed.setter
    def to_be_destroyed(self, value):
        self._to_be_destroyed = value
    
    @property
    def dead(self):
        return self.zone == Zone.GRAVEYARD or self.to_be_destroyed
    
    def _reset_state(self):
        super()._reset_state()
        self.cooldown = 0
        self._turns_in_play = 0
        
    def setup(self):
        super().setup()
        self.events = [OWN_TURN_BEGIN.on(Reduce_Cooldown(SELF))]
        
    def get_controller_dump(self):
        result = super().get_controller_dump()
        result.update({"cooldown": self.cooldown})
        return result
    
    def play(self, *args):
        # Reset cooldown when played
        self.cooldown = 0
        return super().play(*args)
    
    def _set_zone(self, zone):
        if zone == Zone.PLAY:
            # Reset cooldown when played
            self.cooldown = 0
        super()._set_zone(zone)
    
    @property
    def on_cooldown(self):
        return self.cooldown > 0
        
    @property 
    def turns_in_play(self):
        return self._turns_in_play
        
    @turns_in_play.setter
    def turns_in_play(self, value):
        self._turns_in_play = value
        
    def activate(self):
        """
        Activate the location card, setting its cooldown
        """
        self.cooldown = self.location_action_cooldown
        
    def is_usable(self):
        """
        Check if the location is usable (not on cooldown)
        """
        return self.zone == Zone.PLAY and self.cooldown == 0
        
    @property
    def cooldown(self):
        return self._cooldown
        
    @cooldown.setter
    def cooldown(self, value):
        self._cooldown = value 