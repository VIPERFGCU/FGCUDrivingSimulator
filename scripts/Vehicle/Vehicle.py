import math
import carla
import random

from Sensors.LaneInvasionSensor import LaneInvasionSensor
from Vehicle.VehicleController import VehicleController
from Camera.Camera import CameraManager

class Vehicle:
    def __init__(self, world, config_handler, actor_filter, hud):
        self._world = world
        self._config_handler = config_handler
        self._actor_filter = actor_filter
        self._player = None # The carla.Vehicle object
        self.sensors = []   # Contains all of the sensors in an object

        self._hud = hud

        self._camera_manager = None
        self.restart()  # Spawn the vehicle

        self.vehicle_controller = VehicleController(self._player, self._world, False)

        # physics_control = self._player.get_physics_control()
        # physics_control.drag_coefficient = 1.5   # tweak for realism
        # self._player.apply_physics_control(physics_control)

    def tick(self, clock, events):
        self.vehicle_controller.parse_events(clock, events) # Handle the keyboard presses
    
    def set_vehicle_transform(self, new_transform):
        self._player.transform = new_transform
    
    def get_position(self):
        return self._player.get_transform().location
    
    def get_player(self):
        return self._player

    def get_speed(self, miles_per_hour = False):
        speed = 0.0

        v = self._player.get_velocity()
        if miles_per_hour:
            speed = 3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)
        else:   # kmph
            speed = 2.23694 * math.sqrt(v.x**2 + v.y**2 + v.z**2)

        return speed


    def restart(self):
        carla_world = self._world.carla_world

        # Vehicle selection
        random_vehicle = self._config_handler.get_config('AxisMapping', 'random_vehicle', fallback='False') == 'True'
        default_vehicle = self._config_handler.get_config('AxisMapping', 'default_vehicle', fallback='vehicle.dodge.charger_2020')

        if random_vehicle:
            blueprint = random.choice(carla_world.get_blueprint_library().filter(self._actor_filter))
        else:
            blueprint = carla_world.get_blueprint_library().find(default_vehicle)

        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)

        if self._player is not None:
            spawn_point = self._player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self._player = carla_world.try_spawn_actor(blueprint, spawn_point)

        while self._player is None:
            spawn_points = carla_world.get_map().get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self._player = carla_world.try_spawn_actor(blueprint, spawn_point)

        ### CAMERA RESTART ###
        # Keep same camera config if the camera manager exists.
        cam_index = self._camera_manager.index if self._camera_manager is not None else 0
        cam_pos_index = self._camera_manager.transform_index if self._camera_manager is not None else 0

        self._camera_manager = CameraManager(self._player, self._hud)
        self._camera_manager.transform_index = cam_pos_index
        self._camera_manager.set_sensor(cam_index, notify=False)



    def render(self, display):
        self._camera_manager.render(display)

        
    def destroy(self):
        self._camera_manager.sensor.stop()
        self._camera_manager.sensor.destroy()
        
        if self._player is not None:
            self._player.destroy()
        self._player = None