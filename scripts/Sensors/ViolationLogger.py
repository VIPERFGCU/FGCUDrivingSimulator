import carla
import weakref

# from CollisionSensor import CollisionSensor
# from GnssSensor import GnssSensor
# from LaneInvasionSensor import LaneInvasionSensor
from Trial.DataCollector import ScenarioRecorder

class ViolationLogger:
    def __init__(self, recorder : ScenarioRecorder, player, world):
        self._recorder : ScenarioRecorder = recorder
        self._player = player
        self._world = world
        self._sensors = []


    def destroy(self):
        for sensor in self._sensors:
            sensor.stop()
            sensor.destroy()


    def attach_lane_invasion_sensor(self):
        sensor = None

        world = self._player.get_world()
        bp = world.get_blueprint_library().find('sensor.other.lane_invasion')
        sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._player)
        weak_self = weakref.ref(self)
        sensor.listen(lambda event: ViolationLogger._on_lane_invasion(weak_self, event))

        self._sensors.append(sensor)
    
    @staticmethod
    def _on_lane_invasion(weak_self, event):
        self = weak_self()
        if not self:
            return
        
        lane_types = set(x.type for x in event.crossed_lane_markings)
        text = ['%r' % str(x).split()[-1] for x in lane_types]

        log_data = {
            "lanes_crossed" : text
        }
        self._recorder.log_event("violation_lane", log_data)

