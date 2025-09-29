"""
    InputMappingSettings.py
    Author: Siang Chin
    This file handles the loading and storing of axis and key mappings.
    It interfaces with ConfigHandler to obtain this data.
"""

class InputMapping:
    def __init__(self, config_handler):
        self.config_handler = config_handler
        self.axis_mapping = {}
        self.key_mapping = {}
        self.steering_damping = 0.5
        self.throttle_damping = 1.0
        self.brake_damping = 1.0
        self.load_mapping()

    def load_mapping(self):
        axis_mapping, key_mapping, _ = self.config_handler.load_config()

        joystick_controls = ['steering', 'throttle', 'brake']
        for control in joystick_controls:
            if control in axis_mapping and not isinstance(axis_mapping[control], dict):
                axis_mapping[control] = {'joystick': int(axis_mapping[control])}

        for key in list(axis_mapping.keys()):
            if key.startswith('joy_'):
                control = key[4:]
                axis_mapping[control] = {'joystick': int(axis_mapping[key])}
                del axis_mapping[key]

        for damping in ['steering_damping', 'throttle_damping', 'brake_damping']:
            if damping in axis_mapping:
                axis_mapping[damping] = float(axis_mapping[damping])

        self.axis_mapping = axis_mapping
        self.key_mapping = key_mapping
        self.steering_damping = axis_mapping.get('steering_damping', 0.5)
        self.throttle_damping = axis_mapping.get('throttle_damping', 1.0)
        self.brake_damping = axis_mapping.get('brake_damping', 1.0)

    def get_axis(self, control_name):
        return self.axis_mapping.get(control_name, {}).get('joystick')

    def get_key(self, action_name):
        return self.key_mapping.get(action_name)
