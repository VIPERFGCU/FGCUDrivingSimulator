import glob
import os
import sys
import argparse
import collections
import datetime
import logging
import math
import random
import re
import weakref
import time
import string
import json
import csv
from configparser import ConfigParser

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
from carla import ColorConverter as cc
from carla import VehicleLightState as vls

try:
    import pygame
    from pygame.locals import KMOD_CTRL, KMOD_SHIFT
    from pygame.locals import K_0, K_9, K_BACKQUOTE, K_BACKSPACE, K_COMMA, K_DOWN
    from pygame.locals import K_ESCAPE, K_F1, K_LEFT, K_PERIOD, K_RIGHT, K_SLASH
    from pygame.locals import K_SPACE, K_TAB, K_UP, K_a, K_c, K_d, K_h, K_m, K_p, K_q, K_r, K_s, K_w, K_l
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')


class ConfigHandler:
    def __init__(self, config_file='user_config.ini'):
        self.config_file = self.find_config_file(config_file)
        self.config = ConfigParser()

    def find_config_file(self, config_file):
        """Searches for the config file starting from the script's location upwards."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        while True:
            config_path = os.path.join(current_dir, config_file)
            if os.path.isfile(config_path):
                return config_path
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Root directory reached
                break
            current_dir = parent_dir
        raise FileNotFoundError(f"{config_file} not found.")

    def load_config(self):
        self.config.read(self.config_file)
        axis_mapping = {
            'steering': {'joystick': None},
            'throttle': {'joystick': None},
            'brake': {'joystick': None},
            'reverse': {'joystick': None, 'keyboard': None},
            'handbrake': {'joystick': None, 'keyboard': None},
            'hide_hud': {'joystick': None, 'keyboard': None},
            'toggle_headlights': {'joystick': None, 'keyboard': None},
            'steering_damping': 0.5,
            'throttle_damping': 1.0,
            'brake_damping': 1.0,
            'speed_unit': 'km/h',  # Default value
            'height_unit': 'm',  # New setting for height unit
            'random_vehicle': False,
            'default_vehicle': 'vehicle.dodge.charger_2020'
        }
        key_mapping = {}

        trial_settings = {
            'location_x': 246.3,
            'location_y': -27.0,
            'location_z': 1.0,
            'rotation_pitch': 0.0,
            'rotation_yaw': -86.76,
            'rotation_roll': 0.0,
            'speed_limit': 45.0
        }

        if self.config.has_section('AxisMapping'):
            for option in self.config.options('AxisMapping'):
                if option.startswith('joy_'):
                    control = option[4:]
                    if control in axis_mapping:
                        axis_mapping[control]['joystick'] = self.config.getint('AxisMapping', option)
                    else:
                        axis_mapping[control] = {'joystick': self.config.getint('AxisMapping', option)}
                elif option in axis_mapping:
                    value = self.config.get('AxisMapping', option)
                    if value.lower() in ['true', 'false']:
                        axis_mapping[option] = self.config.getboolean('AxisMapping', option)
                    else:
                        try:
                            axis_mapping[option] = float(value)
                        except ValueError:
                            axis_mapping[option] = value

        if self.config.has_section('KeyMapping'):
            for option in self.config.options('KeyMapping'):
                if option.startswith('key_'):
                    control = option[4:]
                    key_mapping[control] = self.config.get('KeyMapping', option)

        if self.config.has_section('TrialSettings'):
            for option in self.config.options('TrialSettings'):
                trial_settings[option] = self.config.getfloat('TrialSettings', option)

        return axis_mapping, key_mapping, trial_settings

    def save_config(self, axis_mapping, key_mapping, trial_settings):
        if not self.config.has_section('AxisMapping'):
            self.config.add_section('AxisMapping')
        if not self.config.has_section('KeyMapping'):
            self.config.add_section('KeyMapping')
        if not self.config.has_section('TrialSettings'):
            self.config.add_section('TrialSettings')

        for option, value in axis_mapping.items():
            if isinstance(value, dict):  # Save joystick and keyboard mapping
                if 'joystick' in value:
                    self.config.set('AxisMapping', f'joy_{option}', str(value['joystick']))
                if 'keyboard' in value:
                    self.config.set('KeyMapping', f'key_{option}', str(value['keyboard']))
            else:
                self.config.set('AxisMapping', option, str(value))

        for option, value in key_mapping.items():
            self.config.set('KeyMapping', f'key_{option}', str(value))

        for option, value in trial_settings.items():
            self.config.set('TrialSettings', option, str(value))

        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def get_config(self, section, option, fallback=None):
        if self.config.has_section(section):
            return self.config.get(section, option, fallback=fallback)
        return fallback



def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


class World(object):
    def __init__(self, carla_world, hud, actor_filter, config_handler):
        self.world = carla_world
        self.hud = hud
        self.player = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.camera_manager = None
        self.config_handler = config_handler
        self._weather_presets = find_weather_presets()
        self._weather_index = 0
        self._actor_filter = actor_filter
        self.brake_light = False
        self.reverse_light = False
        self.headlights_on = False  # Track headlight state
        self.restart()
        self.world.on_tick(hud.on_world_tick)

    def restart(self):
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        
        random_vehicle = self.config_handler.get_config('AxisMapping', 'random_vehicle', fallback='False') == 'True'
        default_vehicle = self.config_handler.get_config('AxisMapping', 'default_vehicle', fallback='vehicle.dodge.charger_2020')

        if random_vehicle:
            blueprint = random.choice(self.world.get_blueprint_library().filter(self._actor_filter))
        else:
            blueprint = self.world.get_blueprint_library().find(default_vehicle)

        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        while self.player is None:
            spawn_points = self.world.get_map().get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        self.init_vehicle_lights()  # Initialize vehicle lights here
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)

    def init_vehicle_lights(self):
        if self.player is not None:
            light_state = vls.NONE
            light_state |= vls.Position
            self.player.set_light_state(carla.VehicleLightState(light_state))

    def toggle_headlights(self):
        if self.player is not None:
            self.headlights_on = not self.headlights_on
            light_state = self.player.get_light_state()
            if self.headlights_on:
                light_state |= vls.LowBeam
            else:
                light_state &= ~vls.LowBeam
            self.player.set_light_state(carla.VehicleLightState(light_state))

    def set_vehicle_light_state(self, brake_light=False, reverse_light=False):
        light_state = self.player.get_light_state()
        if brake_light:
            light_state |= vls.Brake
        else:
            light_state &= ~vls.Brake

        if reverse_light:
            light_state |= vls.Reverse
        else:
            light_state &= ~vls.Reverse

        self.player.set_light_state(carla.VehicleLightState(light_state))

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.player.get_world().set_weather(preset[0])

    def tick(self, clock):
        self.hud.tick(self, clock)

    def render(self, display):
        self.camera_manager.render(display)
        self.hud.render(display)

    def destroy(self):
        sensors = [
            self.camera_manager.sensor,
            self.collision_sensor.sensor,
            self.lane_invasion_sensor.sensor,
            self.gnss_sensor.sensor]
        for sensor in sensors:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()
        if self.player is not None:
            self.player.destroy()


class DualControl(object):
    def __init__(self, world, start_in_autopilot):
        self._autopilot_enabled = start_in_autopilot
        self._control = carla.VehicleControl() if isinstance(world.player, carla.Vehicle) else carla.WalkerControl()
        if isinstance(world.player, carla.Vehicle):
            world.player.set_autopilot(self._autopilot_enabled)
        elif isinstance(world.player, carla.Walker):
            self._autopilot_enabled = False
            self._rotation = world.player.get_transform().rotation
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0
        self.config_handler = world.config_handler
        self.axis_mapping, self.key_mapping = self.load_mapping()
        self.steering_damping = self.axis_mapping.get('steering_damping', 0.5)
        self.throttle_damping = self.axis_mapping.get('throttle_damping', 1.0)
        self.brake_damping = self.axis_mapping.get('brake_damping', 1.0)

        world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)

        pygame.joystick.init()
        try:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        except pygame.error:
            self.joystick = None
            world.hud.notification("No joystick detected. Defaulting to keyboard controls.", seconds=4.0)

    def load_mapping(self):
        axis_mapping, key_mapping, trial_settings = self.config_handler.load_config()
        
        # Convert flat structure to nested structure for joystick controls
        joystick_controls = ['steering', 'throttle', 'brake']
        for control in joystick_controls:
            if control in axis_mapping and not isinstance(axis_mapping[control], dict):
                axis_mapping[control] = {'joystick': int(axis_mapping[control])}
        
        # Handle other joystick mappings
        for key in list(axis_mapping.keys()):
            if key.startswith('joy_'):
                control = key[4:]
                axis_mapping[control] = {'joystick': int(axis_mapping[key])}
                del axis_mapping[key]
        
        # Ensure damping values are floats
        for damping in ['steering_damping', 'throttle_damping', 'brake_damping']:
            if damping in axis_mapping:
                axis_mapping[damping] = float(axis_mapping[damping])
        
        return axis_mapping, key_mapping

    def parse_events(self, world, clock, trial_manager):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.JOYBUTTONDOWN:
                self._handle_joystick_button(event, world)
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                self._handle_key(event, world)
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                trial_manager.handle_event(event)  # Integrate handle_event here

        if not self._autopilot_enabled:
            if isinstance(self._control, carla.VehicleControl):
                self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
                if self.joystick:
                    self._parse_vehicle_wheel()
                self._control.reverse = self._control.gear < 0
            elif isinstance(self._control, carla.WalkerControl):
                self._parse_walker_keys(pygame.key.get_pressed(), clock.get_time())
            world.player.apply_control(self._control)
            self.update_vehicle_lights(world)

    def update_vehicle_lights(self, world):
        brake_light = self._control.brake > 0.0
        reverse_light = self._control.gear < 0
        world.set_vehicle_light_state(brake_light, reverse_light)

    def _handle_joystick_button(self, event, world):
        if self.axis_mapping['reverse']['joystick'] is not None and event.button == self.axis_mapping['reverse']['joystick']:
            self._control.gear = 1 if self._control.reverse else -1
        elif self.axis_mapping['handbrake']['joystick'] is not None and event.button == self.axis_mapping['handbrake']['joystick']:
            self._control.hand_brake = not self._control.hand_brake
        elif self.axis_mapping['hide_hud']['joystick'] is not None and event.button == self.axis_mapping['hide_hud']['joystick']:
            world.hud.toggle_info()
        elif self.axis_mapping['toggle_headlights']['joystick'] is not None and event.button == self.axis_mapping['toggle_headlights']['joystick']:
            world.toggle_headlights()
        elif event.button == 0:
            world.restart()
        elif event.button == 1:
            world.hud.toggle_info()
        elif event.button == 2:
            world.camera_manager.toggle_camera()
        elif event.button == 3:
            world.next_weather()
        elif event.button == 23:
            world.camera_manager.next_sensor()

    def _handle_key(self, event, world):
        if event.key == pygame.K_BACKSPACE:
            world.restart()
        elif event.key == pygame.K_F1:
            world.hud.toggle_info()
        elif event.key == pygame.K_h or (event.key == pygame.K_SLASH and pygame.key.get_mods() & pygame.KMOD_SHIFT):
            world.hud.help.toggle()
        elif event.key == pygame.K_TAB:
            world.camera_manager.toggle_camera()
        elif event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            world.next_weather(reverse=True)
        elif event.key == pygame.K_c:
            world.next_weather()
        elif event.key == pygame.K_BACKQUOTE:
            world.camera_manager.next_sensor()
        elif event.key > pygame.K_0 and event.key <= pygame.K_9:
            world.camera_manager.set_sensor(event.key - 1 - pygame.K_0)
        elif event.key == pygame.K_r:
            world.camera_manager.toggle_recording()
        elif self.key_mapping['reverse'] is not None and event.key == getattr(pygame, f'K_{self.key_mapping["reverse"]}', None):
            self._control.gear = 1 if self._control.reverse else -1
        elif self.key_mapping['handbrake'] is not None and event.key == getattr(pygame, f'K_{self.key_mapping["handbrake"]}', None):
            self._control.hand_brake = not self._control.hand_brake
        elif self.key_mapping['hide_hud'] is not None and event.key == getattr(pygame, f'K_{self.key_mapping["hide_hud"]}', None):
            world.hud.toggle_info()
        elif self.key_mapping['toggle_headlights'] is not None and event.key == getattr(pygame, f'K_{self.key_mapping["toggle_headlights"]}', None):
            world.toggle_headlights()
        if isinstance(self._control, carla.VehicleControl):
            if event.key == pygame.K_q:
                self._control.gear = 1 if self._control.reverse else -1
            elif event.key == pygame.K_m:
                if self._control.manual_gear_shift:
                    self._control.manual_gear_shift = False
                    self._control.gear = world.player.get_control().gear
                    world.hud.notification('Automatic Transmission')
                else:
                    self._control.manual_gear_shift = True
                    self._control.gear = world.player.get_control().gear
                    world.hud.notification('Manual Transmission')
            elif self._control.manual_gear_shift and event.key == pygame.K_COMMA:
                self._control.gear = max(-1, self._control.gear - 1)
            elif self._control.manual_gear_shift and event.key == pygame.K_PERIOD:
                self._control.gear = self._control.gear + 1
            elif event.key == pygame.K_p:
                self._autopilot_enabled = not self._autopilot_enabled
                world.player.set_autopilot(self._autopilot_enabled)
                world.hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
            elif event.key == pygame.K_l:
                # Toggle lights
                self._toggle_vehicle_lights(world)

    def _toggle_vehicle_lights(self, world):
        light_state = world.player.get_light_state()
        if light_state & vls.HighBeam:
            new_state = light_state & ~vls.HighBeam
        else:
            new_state = light_state | vls.HighBeam
        world.player.set_light_state(carla.VehicleLightState(new_state))

    def _parse_vehicle_keys(self, keys, milliseconds):
        self._control.throttle = 1.0 if keys[pygame.K_UP] or keys[pygame.K_w] else 0.0
        steer_increment = 5e-4 * milliseconds
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._steer_cache -= steer_increment
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.brake = 1.0 if keys[pygame.K_DOWN] or keys[pygame.K_s] else 0.0
        self._control.hand_brake = keys[pygame.K_SPACE]

    def _parse_vehicle_wheel(self):
        numAxes = self.joystick.get_numaxes()
        jsInputs = [float(self.joystick.get_axis(i)) for i in range(numAxes)]

        steering_axis = self.axis_mapping.get('steering', {}).get('joystick')
        throttle_axis = self.axis_mapping.get('throttle', {}).get('joystick')
        brake_axis = self.axis_mapping.get('brake', {}).get('joystick')

        if steering_axis is not None and throttle_axis is not None and brake_axis is not None:
            # Apply damping to the inputs
            steerCmd = self.steering_damping * math.tan(1.1 * jsInputs[steering_axis])
            throttleCmd = self.throttle_damping * (1.6 + (2.05 * math.log10(-0.7 * jsInputs[throttle_axis] + 1.4) - 1.2) / 0.92)
            brakeCmd = self.brake_damping * (1.6 + (2.05 * math.log10(-0.7 * jsInputs[brake_axis] + 1.4) - 1.2) / 0.92)

            throttleCmd = max(0, min(1, throttleCmd))
            brakeCmd = max(0, min(1, brakeCmd))

            self._control.steer = steerCmd
            self._control.brake = brakeCmd
            self._control.throttle = throttleCmd

    def _parse_walker_keys(self, keys, milliseconds):
        self._control.speed = 0.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self._control.speed = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._control.speed = .01
            self._rotation.yaw -= 0.08 * milliseconds
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._control.speed = .01
            self._rotation.yaw += 0.08 * milliseconds
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self._control.speed = 5.556 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 2.778
        self._control.jump = keys[pygame.K_SPACE]
        self._rotation.yaw = round(self._rotation.yaw, 1)
        self._control.direction = self._rotation.get_forward_vector()

    @staticmethod
    def _is_quit_shortcut(key):
        return key == pygame.K_ESCAPE or (key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL)


class HUD(object):
    def __init__(self, width, height, config_handler):
        self.dim = (width, height)
        self.config_handler = config_handler
        self.speed_unit = self.config_handler.get_config('Settings', 'speed_unit', fallback='km/h')
        self.height_unit = self.config_handler.get_config('Settings', 'height_unit', fallback='m')
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 12 if os.name == 'nt' else 14)
        self._notifications = FadingText(font, (width, 40), (0, height - 40))
        self.help = HelpText(pygame.font.Font(mono, 24), width, height)
        self.server_fps = 0
        self.frame = 0
        self.simulation_time = 0
        self._show_info = True
        self._info_text = []
        self._server_clock = pygame.time.Clock()

    def on_world_tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        self.frame = timestamp.frame
        self.simulation_time = timestamp.elapsed_seconds

    def tick(self, world, clock):
        self._notifications.tick(world, clock)
        if not self._show_info:
            return
        t = world.player.get_transform()
        v = world.player.get_velocity()
        c = world.player.get_control()
        heading = 'N' if abs(t.rotation.yaw) < 89.5 else ''
        heading += 'S' if abs(t.rotation.yaw) > 90.5 else ''
        heading += 'E' if 179.5 > t.rotation.yaw > 0.5 else ''
        heading += 'W' if -0.5 > t.rotation.yaw > -179.5 else ''
        colhist = world.collision_sensor.get_collision_history()
        collision = [colhist[x + self.frame - 200] for x in range(0, 200)]
        max_col = max(1.0, max(collision))
        collision = [x / max_col for x in collision]
        vehicles = world.world.get_actors().filter('vehicle.*')
        
        if self.speed_unit == 'km/h':
            speed = 3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)
            speed_text = 'Speed:   % 15.0f km/h' % speed
        else:
            speed = 2.23694 * math.sqrt(v.x**2 + v.y**2 + v.z**2)
            speed_text = 'Speed:   % 15.0f mph' % speed

        height = t.location.z
        if self.height_unit == 'ft':
            height *= 3.28084
            height_text = 'Height:  % 18.0f ft' % height
        else:
            height_text = 'Height:  % 18.0f m' % height

        rotation = t.rotation
        rotation_text = 'Rotation: %.2f, %.2f, %.2f' % (rotation.pitch, rotation.yaw, rotation.roll)

        self._info_text = [
            'Server:  % 16.0f FPS' % self.server_fps,
            'Client:  % 16.0f FPS' % clock.get_fps(),
            '',
            'Vehicle: % 20s' % get_actor_display_name(world.player, truncate=20),
            'Map:     % 20s' % world.world.get_map().name.split('/')[-1],
            'Simulation time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)),
            '',
            speed_text,
            u'Heading:% 16.0f\N{DEGREE SIGN} % 2s' % (t.rotation.yaw, heading),
            'Location:% 20s' % ('(% 5.1f, % 5.1f)' % (t.location.x, t.location.y)),
            'GNSS:% 24s' % ('(% 2.6f, % 3.6f)' % (world.gnss_sensor.lat, world.gnss_sensor.lon)),
            rotation_text,
            height_text,
            '']
        if isinstance(c, carla.VehicleControl):
            self._info_text += [
                ('Throttle:', c.throttle, 0.0, 1.0),
                ('Steer:', c.steer, -1.0, 1.0),
                ('Brake:', c.brake, 0.0, 1.0),
                ('Reverse:', c.reverse),
                ('Hand brake:', c.hand_brake),
                ('Manual:', c.manual_gear_shift),
                'Gear:        %s' % {-1: 'R', 0: 'N'}.get(c.gear, c.gear)]
        elif isinstance(c, carla.WalkerControl):
            self._info_text += [
                ('Speed:', c.speed, 0.0, 5.556),
                ('Jump:', c.jump)]
        self._info_text += [
            '',
            'Collision:',
            collision,
            '',
            'Number of vehicles: % 8d' % len(vehicles)]
        if len(vehicles) > 1:
            self._info_text += ['Nearby vehicles:']
            distance = lambda l: math.sqrt((l.x - t.location.x)**2 + (l.y - t.location.y)**2 + (l.z - t.location.z)**2)
            vehicles = [(distance(x.get_location()), x) for x in vehicles if x.id != world.player.id]
            for d, vehicle in sorted(vehicles):
                if d > 200.0:
                    break
                vehicle_type = get_actor_display_name(vehicle, truncate=22)
                self._info_text.append('% 4dm %s' % (d, vehicle_type))

    def toggle_info(self):
        self._show_info = not self._show_info

    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    def error(self, text):
        self._notifications.set_text('Error: %s' % text, (255, 0, 0))

    def render(self, display):
        if self._show_info:
            info_surface = pygame.Surface((220, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            for item in self._info_text:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, list):
                    if len(item) > 1:
                        points = [(x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                        pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                    item = None
                    v_offset += 18
                elif isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect_border, 1)
                        f = (item[1] - item[2]) / (item[3] - item[2])
                        if item[2] < 0.0:
                            rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                        else:
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect)
                    item = item[0]
                if item:  # At this point has to be a str.
                    surface = self._font_mono.render(item, True, (255, 255, 255))
                    display.blit(surface, (8, v_offset))
                v_offset += 18
        self._notifications.render(display)
        self.help.render(display)


class FadingText(object):
    def __init__(self, font, dim, pos):
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        display.blit(self.surface, self.pos)


class HelpText(object):
    def __init__(self, font, width, height):
        help_lines = [
            "Welcome to CARLA manual control with steering wheel Logitech G29.",
            "To drive start by pressing the brake pedal.",
            "Change your wheel_config.ini according to your steering wheel.",
            "To find out the values of your steering wheel use jstest-gtk in Ubuntu.",
            "",
            "Controls:",
            "  - Arrow keys or WASD: Control the vehicle",
            "  - Space: Hand brake",
            "  - Backspace: Restart",
            "  - F1: Toggle info",
            "  - H or /?: Toggle help",
            "  - Tab: Change camera",
            "  - C: Change weather",
            "  - Backquote: Next sensor",
            "  - R: Toggle recording",
            "  - Q: Toggle reverse gear",
            "  - M: Toggle manual transmission",
            "  - , or .: Change gear in manual transmission",
            "  - P: Toggle autopilot",
            "  - L: Toggle vehicle lights",
            "  - J: Toggle headlights"  # Added toggle for headlights
        ]

        self.font = font
        self.dim = (680, len(help_lines) * 22 + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill((0, 0, 0, 0))

        for n, line in enumerate(help_lines):
            text_texture = self.font.render(line, True, (255, 255, 255))
            self.surface.blit(text_texture, (22, n * 22))
        self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        self._render = not self._render

    def render(self, display):
        if self._render:
            display.blit(self.surface, self.pos)


class CollisionSensor(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self.history = []
        self._parent = parent_actor
        self.hud = hud
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.collision')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: CollisionSensor._on_collision(weak_self, event))

    def get_collision_history(self):
        history = collections.defaultdict(int)
        for frame, intensity in self.history:
            history[frame] += intensity
        return history

    @staticmethod
    def _on_collision(weak_self, event):
        self = weak_self()
        if not self:
            return
        actor_type = get_actor_display_name(event.other_actor)
        self.hud.notification('Collision with %r' % actor_type)
        impulse = event.normal_impulse
        intensity = math.sqrt(impulse.x**2 + impulse.y**2 + impulse.z**2)
        self.history.append((event.frame, intensity))
        if len(self.history) > 4000:
            self.history.pop(0)


class LaneInvasionSensor(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self._parent = parent_actor
        self.hud = hud
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.lane_invasion')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: LaneInvasionSensor._on_invasion(weak_self, event))

    @staticmethod
    def _on_invasion(weak_self, event):
        self = weak_self()
        if not self:
            return
        lane_types = set(x.type for x in event.crossed_lane_markings)
        text = ['%r' % str(x).split()[-1] for x in lane_types]
        self.hud.notification('Crossed line %s' % ' and '.join(text))


class GnssSensor(object):
    def __init__(self, parent_actor):
        self.sensor = None
        self._parent = parent_actor
        self.lat = 0.0
        self.lon = 0.0
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.gnss')
        self.sensor = world.spawn_actor(bp, carla.Transform(carla.Location(x=1.0, z=2.8)), attach_to=self._parent)
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: GnssSensor._on_gnss_event(weak_self, event))

    @staticmethod
    def _on_gnss_event(weak_self, event):
        self = weak_self()
        if not self:
            return
        self.lat = event.latitude
        self.lon = event.longitude


class CameraManager(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self.surface = None
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        self._camera_transforms = [
            carla.Transform(carla.Location(x=-5.5, z=2.8), carla.Rotation(pitch=-15)),
            carla.Transform(carla.Location(x=1.6, z=1.7))]
        self.transform_index = 1
        self.sensors = [
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB'],
            ['sensor.camera.depth', cc.Raw, 'Camera Depth (Raw)'],
            ['sensor.camera.depth', cc.Depth, 'Camera Depth (Gray Scale)'],
            ['sensor.camera.depth', cc.LogarithmicDepth, 'Camera Depth (Logarithmic Gray Scale)'],
            ['sensor.camera.semantic_segmentation', cc.Raw, 'Camera Semantic Segmentation (Raw)'],
            ['sensor.camera.semantic_segmentation', cc.CityScapesPalette,
                'Camera Semantic Segmentation (CityScapes Palette)'],
            ['sensor.lidar.ray_cast', None, 'Lidar (Ray-Cast)']]
        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        for item in self.sensors:
            bp = bp_library.find(item[0])
            if item[0].startswith('sensor.camera'):
                bp.set_attribute('image_size_x', str(hud.dim[0]))
                bp.set_attribute('image_size_y', str(hud.dim[1]))
            elif item[0].startswith('sensor.lidar'):
                bp.set_attribute('range', '50')
            item.append(bp)
        self.index = None

    def toggle_camera(self):
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.sensor.set_transform(self._camera_transforms[self.transform_index])

    def set_sensor(self, index, notify=True):
        index = index % len(self.sensors)
        needs_respawn = True if self.index is None \
            else self.sensors[index][0] != self.sensors[self.index][0]
        if needs_respawn:
            if self.sensor is not None:
                self.sensor.destroy()
                self.surface = None
            self.sensor = self._parent.get_world().spawn_actor(
                self.sensors[index][-1],
                self._camera_transforms[self.transform_index],
                attach_to=self._parent)
            weak_self = weakref.ref(self)
            self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))
        if notify:
            self.hud.notification(self.sensors[index][2])
        self.index = index

    def next_sensor(self):
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        self.recording = not self.recording
        self.hud.notification('Recording %s' % ('On' if self.recording else 'Off'))

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self:
            return
        if self.sensors[self.index][0].startswith('sensor.lidar'):
            points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
            points = np.reshape(points, (int(points.shape[0] / 4), 4))
            lidar_data = np.array(points[:, :2])
            lidar_data *= min(self.hud.dim) / 100.0
            lidar_data += (0.5 * self.hud.dim[0], 0.5 * self.hud.dim[1])
            lidar_data = np.fabs(lidar_data)  # pylint: disable=E1111
            lidar_data = lidar_data.astype(np.int32)
            lidar_data = np.reshape(lidar_data, (-1, 2))
            lidar_img_size = (self.hud.dim[0], self.hud.dim[1], 3)
            lidar_img = np.zeros(lidar_img_size)
            lidar_img[tuple(lidar_data.T)] = (255, 255, 255)
            self.surface = pygame.surfarray.make_surface(lidar_img)
        else:
            image.convert(self.sensors[self.index][1])
            array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (image.height, image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self.recording:
            image.save_to_disk('_out/%08d' % image.frame)

class TrialManager:
    def __init__(self, hud, config_handler, player, world):
        # Initialize the data directory first
        self.data_dir = os.path.join(os.path.dirname(__file__), 'scripts', 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Initialize the violation events CSV file path
        self.events_csv_file_path = self.get_events_csv_file_path()
        self.init_events_csv()

        # Now proceed with the rest of the initialization
        self.hud = hud
        self.trial_active = False
        self.start_time = None
        self.end_time = None
        self.violation_start = None
        self.violation_durations = []
        self.violation_count = 0
        self.config_handler = config_handler
        self.trial_settings = self.config_handler.load_config()[2]
        self.max_speed = self.trial_settings.get('speed_limit', 45.0)  # Speed limit in miles per hour
        self.trial_results = {}
        self.display_results = False
        self.start_screen = False
        self.current_speed = 0.0
        self.speeding_warning = False
        self.max_speed_during_run = 0.0
        self.min_speed_during_run = float('inf')

        # World and weather presets
        self.world = world
        self.weather_preset = world._weather_presets[world._weather_index][1]

        # Session and trial codes
        self.session_code = self.generate_code()  # Generate once per session
        self.trial_code = None

        # User name management
        self.user_name = ""
        self.new_user_name = ""  # For adding a new user
        self.user_names = []
        self.active_input = False  # To track if the text box is active for input
        self.dropdown_open = False  # To track if the dropdown is open
        self.load_user_names()  # Load user names from memory file
        self.selected_name_index = len(self.user_names) - 1  # Automatically select the last used name
        if self.selected_name_index >= 0:
            self.user_name = self.user_names[self.selected_name_index]

        # Initialize data_to_write list
        self.data_to_write = []  # List to store data to be written to CSV

        # Open today's file or create a new one
        self.csv_file_path = self.get_daily_csv_file_path()
        self.csv_file = open(self.csv_file_path, 'a', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        
        # Write the header to the CSV only if the file is new/empty
        if os.path.getsize(self.csv_file_path) == 0:
            self.csv_writer.writerow([
                'User Name', 'Session Code', 'Trial Code', 'Unix Timestamp',
                'Time Elapsed', 'Speed', 'X', 'Y', 'Z', 'Pitch', 'Yaw', 'Roll', 'Heading (Degrees)', 'Heading (Cardinal)', 'Vehicle'
            ])

        # Store the vehicle type
        self.vehicle_type = get_actor_display_name(player)

    def get_events_csv_file_path(self):
        """Generate a file path for the events CSV file based on the current date."""
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        return os.path.join(self.data_dir, f'Trial_events_{date_str}.csv')

    def init_events_csv(self):
        """Initialize the events CSV file with a header if it doesn't exist."""
        if not os.path.exists(self.events_csv_file_path) or os.path.getsize(self.events_csv_file_path) == 0:
            with open(self.events_csv_file_path, 'a', newline='') as events_file:
                events_writer = csv.writer(events_file)
                events_writer.writerow([
                    'Session Code', 'Trial Code', 'Unix Timestamp',
                    'Event Type', 'Violation Duration', 'X', 'Y', 'Z', 'Pitch', 'Yaw', 'Roll'
                ])

    def record_event(self, event_type, violation_duration, location, rotation):
        """Record an event in the events CSV file."""
        timestamp = int(time.time())
        with open(self.events_csv_file_path, 'a', newline='') as events_file:
            events_writer = csv.writer(events_file)
            events_writer.writerow([
                self.session_code, self.trial_code, timestamp,
                event_type, violation_duration, location.x, location.y, location.z, 
                rotation.pitch, rotation.yaw, rotation.roll
            ])

    def generate_code(self, length=8):
        """Generates a random code of letters and digits."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def get_daily_csv_file_path(self):
        # Generate a file name based on the current date
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        return os.path.join(self.data_dir, f'runs_data_{date_str}.csv')

    def get_totals_csv_file_path(self):
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        return os.path.join(self.data_dir, f'totals_data_{date_str}.csv')

    def load_user_names(self):
        """Load user names from the memory file."""
        memory_dir = os.path.join(self.data_dir, 'memory')
        memory_file = os.path.join(memory_dir, 'user_names.json')

        # Ensure the 'memory' directory exists
        if not os.path.exists(memory_dir):
            os.makedirs(memory_dir)

        # Clear current list of names to avoid residuals
        self.user_names = []

        # Load names from the memory file if it exists
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as file:
                self.user_names = json.load(file)
                print(f"Loaded user names from memory: {self.user_names}")
                self.selected_name_index = len(self.user_names) - 1  # Auto-load the last used name
        else:
            print("Memory file not found or empty.")

    def save_user_name(self, name):
        """Add a new user name to the memory file and update the dropdown list."""
        if name and name not in self.user_names:
            self.user_names.append(name)
            memory_dir = os.path.join(self.data_dir, 'memory')
            memory_file = os.path.join(memory_dir, 'user_names.json')
            with open(memory_file, 'w') as file:
                json.dump(self.user_names, file)
            print(f"Added new user name: {name}")
        self.user_name = name
        self.selected_name_index = self.user_names.index(name)  # Set the selected name in the dropdown

    def start_trial(self, player):
        self.start_screen = True
        self.trial_active = False
        self.hud.notification("Press Enter to Start Run", seconds=10)
        # Teleport the player to the start location and rotation
        teleport_location = carla.Location(
            x=self.trial_settings.get('location_x', 246.3), 
            y=self.trial_settings.get('location_y', -27.0), 
            z=self.trial_settings.get('location_z', 1.0)
        )
        teleport_rotation = carla.Rotation(
            pitch=self.trial_settings.get('rotation_pitch', 0.0), 
            yaw=self.trial_settings.get('rotation_yaw', -86.76), 
            roll=self.trial_settings.get('rotation_roll', 0.0)
        )
        transform = carla.Transform(teleport_location, teleport_rotation)
        player.set_transform(transform)

    def initiate_trial(self):
        self.trial_active = True
        self.start_time = time.time()
        self.violation_start = None
        self.violation_durations = []
        self.violation_count = 0
        self.display_results = False
        self.start_screen = False
        self.speeding_warning = False
        self.max_speed_during_run = 0.0
        self.min_speed_during_run = float('inf')

        # Generate a new trial code for this trial
        self.trial_code = self.generate_code()

    def end_trial(self):
        self.trial_active = False
        self.end_time = time.time()
        self.calculate_results()
        self.display_results = True

        # Write the collected data to the CSV file
        if self.csv_file and self.csv_writer:
            self.csv_writer.writerows(self.data_to_write)

        # Reset the data_to_write list for the next trial
        self.data_to_write = []

        # Write totals to the totals CSV file
        self.write_totals_to_csv()

    def calculate_results(self):
        trial_duration = self.end_time - self.start_time
        avg_speed = sum([speed for _, speed in self.violation_durations]) / len(self.violation_durations) if self.violation_durations else 0
        avg_violation_duration = sum([duration for duration, _ in self.violation_durations]) / len(self.violation_durations) if self.violation_durations else 0

        self.trial_results = {
            'trial_duration': trial_duration,
            'avg_speed': avg_speed,
            'avg_violation_duration': avg_violation_duration,
            'violation_count': self.violation_count
        }

    def write_totals_to_csv(self):
        totals_csv_path = self.get_totals_csv_file_path()
        trial_start_date = datetime.datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')
        with open(totals_csv_path, 'a', newline='') as totals_file:
            totals_writer = csv.writer(totals_file)
            if os.path.getsize(totals_csv_path) == 0:
                totals_writer.writerow([
                    'User Name', 'Session Code', 'Trial Code', 'Trial Start Date', 'Trial Duration',
                    'Average Speed', 'Max Speed', 'Min Speed', 'Violation Count', 
                    'Average Violation Duration', 'Vehicle', 'Weather Preset'
                ])
            totals_writer.writerow([
                self.user_name,
                self.session_code,
                self.trial_code,
                trial_start_date,
                self.format_time(self.trial_results['trial_duration']),
                round(self.trial_results['avg_speed'], 2),  # Store as floating point
                round(self.max_speed_during_run, 2),  # Store as floating point
                round(self.min_speed_during_run, 2),  # Store as floating point
                self.trial_results['violation_count'],
                f"{self.trial_results['avg_violation_duration']:.2f} seconds",
                self.vehicle_type,
                self.weather_preset
            ])

    def track_speed(self, speed, player):
        self.current_speed = speed
        if self.trial_active:
            self.max_speed_during_run = max(self.max_speed_during_run, speed)
            self.min_speed_during_run = min(self.min_speed_during_run, speed)

            if speed > self.max_speed:
                if self.violation_start is None:
                    self.violation_start = time.time()
                    self.violation_count += 1
                self.speeding_warning = True
            else:
                if self.violation_start is not None:
                    violation_end = time.time()
                    violation_duration = violation_end - self.violation_start
                    location = player.get_transform().location
                    rotation = player.get_transform().rotation
                    self.violation_durations.append((violation_duration, speed))
                    # Record the violation event
                    self.record_event('violation', violation_duration, location, rotation)
                    self.violation_start = None
                self.speeding_warning = False

            # Collect data every 500 milliseconds
            if time.time() - self.start_time >= len(self.data_to_write) * 0.5:
                location = player.get_transform().location
                rotation = player.get_transform().rotation
                timestamp = int(time.time())

                # Calculate heading (in degrees) and cardinal direction
                heading_degrees = rotation.yaw
                heading_cardinal = self.calculate_heading_cardinal(rotation.yaw)
                
                # Add data row with the new columns
                self.data_to_write.append([
                    self.user_name, self.session_code, self.trial_code, timestamp,
                    round(time.time() - self.start_time, 2), speed,  # Store as floating point
                    location.x, location.y, location.z,
                    rotation.pitch, rotation.yaw, rotation.roll,
                    heading_degrees, heading_cardinal, self.vehicle_type
                ])
    
    @staticmethod
    def calculate_heading_cardinal(yaw):
        if abs(yaw) < 45:
            return 'N'
        elif 45 <= yaw < 135:
            return 'E'
        elif abs(yaw) >= 135:
            return 'S'
        else:
            return 'W'

    def render_results(self, display):
        if self.display_results:
            font = pygame.font.Font(None, 36)
            results_text = [
                f"Trial Duration: {self.format_time(self.trial_results['trial_duration'])}",
                f"Average Speed: {int(round(self.trial_results['avg_speed']))}",  # Display as integer
                f"Average Violation Duration: {self.trial_results['avg_violation_duration']:.2f} seconds",
                f"Violation Count: {self.trial_results['violation_count']}",
                f"Max Speed: {int(round(self.max_speed_during_run))}",  # Display as integer
                f"Min Speed: {int(round(self.min_speed_during_run))}"  # Display as integer
            ]
            background = pygame.Surface((display.get_width(), display.get_height()))
            background.fill((0, 0, 0))
            background.set_alpha(150)
            display.blit(background, (0, 0))
            y_offset = display.get_height() // 2 - len(results_text) * 20
            for line in results_text:
                text_surface = font.render(line, True, (255, 255, 255))
                display.blit(text_surface, (display.get_width() // 2 - text_surface.get_width() // 2, y_offset))
                y_offset += 40

    def render_start_screen(self, display):
        if self.start_screen:
            font = pygame.font.Font(None, 36)
            text_surface = font.render("Press Enter to Start Run", True, (255, 255, 255))
            text_surface.set_alpha(200)
            background = pygame.Surface((display.get_width(), display.get_height()))
            background.fill((0, 0, 0))
            background.set_alpha(150)
            display.blit(background, (0, 0))
            display.blit(text_surface, (display.get_width() // 2 - text_surface.get_width() // 2, display.get_height() // 2 - text_surface.get_height() // 2))

            # Draw the text box and dropdown for the username
            self.render_name_input(display)

    def render_name_input(self, display):
        font = pygame.font.Font(None, 32)
        input_box = pygame.Rect(640 - 100, 360 + 50, 200, 32)
        add_button = pygame.Rect(input_box.x + 210, input_box.y, 80, 32)
        dropdown_rect = pygame.Rect(640 - 100, 360 + 82, 200, len(self.user_names) * 32)

        pygame.draw.rect(display, (255, 255, 255), input_box, 0)
        pygame.draw.rect(display, (0, 0, 0), input_box, 2)
        pygame.draw.rect(display, (0, 0, 0), add_button, 2)

        text_color = (0, 0, 0) if self.active_input else (0, 0, 0)
        name_surface = font.render(self.new_user_name if self.active_input else self.user_name, True, text_color)
        display.blit(name_surface, (input_box.x + 5, input_box.y + 5))

        add_text = font.render("Add", True, (0, 0, 0))
        display.blit(add_text, (add_button.x + 5, add_button.y + 5))

        # Draw dropdown list
        if self.dropdown_open:
            pygame.draw.rect(display, (255, 255, 255), dropdown_rect, 0)
            pygame.draw.rect(display, (0, 0, 0), dropdown_rect, 2)
            for i, name in enumerate(self.user_names):
                name_surface = font.render(name, True, (0, 0, 0))
                display.blit(name_surface, (dropdown_rect.x + 5, dropdown_rect.y + 5 + i * 32))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.display_results:
                    self.display_results = False  # Just close the results screen
                    return  # Don't start a new trial immediately
                elif self.start_screen:
                    self.initiate_trial()
            elif event.key == pygame.K_SPACE and self.trial_active:
                self.end_trial()
            # Handle other events...

        if event.type == pygame.MOUSEBUTTONDOWN:
            input_box = pygame.Rect(640 - 100, 360 + 50, 200, 32)
            add_button = pygame.Rect(input_box.x + 210, input_box.y, 80, 32)
            dropdown_rect = pygame.Rect(640 - 100, 360 + 82, 200, len(self.user_names) * 32)
            if input_box.collidepoint(event.pos):
                self.active_input = True
                self.dropdown_open = not self.dropdown_open  # Toggle dropdown visibility when clicking on the input box
            elif add_button.collidepoint(event.pos):
                if self.new_user_name.strip():  # Ensure that the user name is not empty
                    self.save_user_name(self.new_user_name)
                    self.new_user_name = ""  # Clear the input after saving
                self.dropdown_open = False
            elif dropdown_rect.collidepoint(event.pos) and self.dropdown_open:
                relative_y = event.pos[1] - dropdown_rect.y
                self.selected_name_index = relative_y // 32
                self.user_name = self.user_names[self.selected_name_index]
                self.dropdown_open = False
            else:
                self.active_input = False
                self.dropdown_open = False

        if event.type == pygame.KEYDOWN:
            if self.active_input:
                if event.key == pygame.K_RETURN:
                    if self.new_user_name.strip():  # Ensure that the user name is not empty
                        self.save_user_name(self.new_user_name)
                        self.new_user_name = ""  # Clear the input after saving
                    self.active_input = False
                elif event.key == pygame.K_BACKSPACE:
                    self.new_user_name = self.new_user_name[:-1]
                else:
                    self.new_user_name += event.unicode
            elif self.dropdown_open:
                if event.key == pygame.K_DOWN:
                    self.selected_name_index = (self.selected_name_index + 1) % len(self.user_names)
                    self.user_name = self.user_names[self.selected_name_index]
                elif event.key == pygame.K_UP:
                    self.selected_name_index = (self.selected_name_index - 1) % len(self.user_names)
                    self.user_name = self.user_names[self.selected_name_index]

    def render_timer(self, display):
        if self.trial_active:
            font = pygame.font.Font(None, 36)
            elapsed_time = time.time() - self.start_time
            timer_text = f"Time: {self.format_time(elapsed_time)}"
            text_surface = font.render(timer_text, True, (255, 255, 255))
            display.blit(text_surface, (display.get_width() - text_surface.get_width() - 20, 20))
            
            speed_text = f"Speed: {int(round(self.current_speed))} mph"  # Display as integer
            speed_surface = font.render(speed_text, True, (255, 255, 255))
            display.blit(speed_surface, (display.get_width() - speed_surface.get_width() - 20, 60))
            
            violation_text = f"Violations: {self.violation_count}"
            violation_surface = font.render(violation_text, True, (255, 255, 255))
            display.blit(violation_surface, (display.get_width() - violation_surface.get_width() - 20, 100))

            if self.speeding_warning:
                warning_text = "You are exceeding the speed limit!"
                warning_surface = font.render(warning_text, True, (255, 0, 0))
                display.blit(warning_surface, (display.get_width() // 2 - warning_surface.get_width() // 2, display.get_height() // 2 - warning_surface.get_height() // 2))

    @staticmethod
    def format_time(seconds):
        milliseconds = int((seconds % 1) * 100)
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02}:{seconds:02}:{milliseconds:02}"

    def close_session(self):
        # Close the runs CSV file when the session ends
        if self.csv_file:
            self.csv_file.close()


def game_loop(args):
    pygame.init()
    pygame.font.init()
    world = None

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(60)

        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        # Load the specified town
        town_name = args.town if args.town else 'Town03'
        client.load_world(town_name)

        config_handler = ConfigHandler()
        config_handler.load_config()

        hud = HUD(args.width, args.height, config_handler)
        world = World(client.get_world(), hud, args.filter, config_handler)
        trial_manager = TrialManager(hud, config_handler, world.player, world)  # Pass the 'world' object here
        controller = DualControl(world, args.autopilot)

        clock = pygame.time.Clock()
        while True:
            clock.tick_busy_loop(60)
            if controller.parse_events(world, clock, trial_manager):
                return

            # Handle trial start and initiation
            keys = pygame.key.get_pressed()
            if keys[pygame.K_KP1]:
                trial_manager.start_trial(world.player)
            if keys[pygame.K_RETURN] and trial_manager.start_screen:
                trial_manager.initiate_trial()
            if keys[pygame.K_SPACE] and trial_manager.trial_active:
                trial_manager.end_trial()
            if keys[pygame.K_RETURN] and trial_manager.display_results:
                trial_manager.start_trial(world.player)

            # Track and update speed during the trial
            v = world.player.get_velocity()
            speed = 2.23694 * math.sqrt(v.x**2 + v.y**2 + v.z**2)  # Convert m/s to mph
            trial_manager.track_speed(speed, world.player)  # Pass world.player here as well

            world.tick(clock)
            world.render(display)
            trial_manager.render_start_screen(display)
            trial_manager.render_timer(display)
            trial_manager.render_results(display)
            pygame.display.flip()

    finally:
        if world is not None:
            world.destroy()

        pygame.quit()


def main():
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '--town',
        metavar='TOWN',
        default='Town03',
        help='Specify which town to load (default: "Town03")')
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    try:
        game_loop(args)
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':
    main()