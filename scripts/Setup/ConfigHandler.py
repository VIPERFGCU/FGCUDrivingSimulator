"""
    filename: Camera.py
    Author: Siang Chin
    This reads the configuration file, default set to user_config.ini, and
    stores all settings for later setup.
"""

import os
from configparser import ConfigParser   # To read the .ini file

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
            'speed_limit': 45.0,
            'max_speed_limit' : 50.0,
            'data_save_location' : r"C:\\carla_env\\fgcu-carla-UPDATED\\scripts\\Setup\\"
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
                try:
                    trial_settings[option] = self.config.getfloat('TrialSettings', option)  # Make it a float if possible
                except:
                    trial_settings[option] = self.config.get('TrialSettings', option)   # Leave it as a string otherwise

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
