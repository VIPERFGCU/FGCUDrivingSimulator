"""
    filename: LaneInvasionSensor.py
    author: Siang Chin
    This file has no changes from the default carla example code.
    It will call _on_invasion whenever the player crosses a line.
"""


import weakref
import carla

class LaneInvasionSensor(object):
    def __init__(self, parent_actor):
        self.sensor = None
        self._parent = parent_actor
        # self.hud = hud
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.lane_invasion')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: LaneInvasionSensor._on_invasion(weak_self, event))
        
        # Flag that turns true when a line is cross
        self._crossed_line = False

    def is_line_just_crossed(self):
        _crossed_line = self.crossed_line
        
        # Clear flag
        self._crossed_line = False

        return _crossed_line

    @staticmethod
    def _on_invasion(weak_self, event):
        self = weak_self()
        if not self:
            return
        lane_types = set(x.type for x in event.crossed_lane_markings)
        text = ['%r' % str(x).split()[-1] for x in lane_types]
        self.hud.notification('Crossed line %s' % ' and '.join(text))
        _crossed_line = True
