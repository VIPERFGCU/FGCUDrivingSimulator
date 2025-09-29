
from CollisionSensor import CollisionSensor
from GnssSensor import GnssSensor


class SensorManager:
    def __init__(self, player, hud):
        self.collision_sensor = CollisionSensor(player, hud)
        self.gnss_sensor = GnssSensor(player)

    def destroy(self):
        sensors = [
            self.camera_manager.sensor,
            self.collision_sensor.sensor,
            self.lane_invasion_sensor.sensor,
            self.gnss_sensor.sensor,
        ]
        for sensor in sensors:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()
