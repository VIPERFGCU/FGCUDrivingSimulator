"""
    filename: VehicleInputHandler.py
    author: Siang Chin
"""

import pygame
from math import log10, tan                 # For steering damping. See parse_joystick_input()

from .InputMappingSettings import InputMapping
from .VehicleSteering import VehicleControlState

class VehicleInputHandler:
    def __init__(self, input_mapping: InputMapping, control_state: VehicleControlState, joystick=None):
        self.input_mapping = input_mapping
        self.control_state = control_state
        self.joystick = joystick

    def parse_keyboard_input(self, keys, milliseconds):
        throttle = 1.0 if keys[pygame.K_UP] or keys[pygame.K_w] else 0.0
        self.control_state.set_throttle(throttle)

        steer_increment = 5e-4 * milliseconds
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.control_state.update_steer_cache(-steer_increment)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.control_state.update_steer_cache(steer_increment)
        else:
            self.control_state.reset_steer_cache()

        brake = 1.0 if keys[pygame.K_DOWN] or keys[pygame.K_s] else 0.0
        self.control_state.set_brake(brake)

        hand_brake = keys[pygame.K_SPACE]
        self.control_state.set_hand_brake(hand_brake)

    def parse_joystick_input(self):
        if not self.joystick:
            return

        num_axes = self.joystick.get_numaxes()
        js_inputs = [float(self.joystick.get_axis(i)) for i in range(num_axes)]

        steering_axis = self.input_mapping.get_axis('steering')
        throttle_axis = self.input_mapping.get_axis('throttle')
        brake_axis = self.input_mapping.get_axis('brake')

        if steering_axis is None or throttle_axis is None or brake_axis is None:
            return

        steering_damping = self.input_mapping.steering_damping
        throttle_damping = self.input_mapping.throttle_damping
        brake_damping = self.input_mapping.brake_damping

        steer_cmd = steering_damping * tan(1.1 * js_inputs[steering_axis])
        throttle_cmd = throttle_damping * (1.6 + (2.05 * log10(-0.7 * js_inputs[throttle_axis] + 1.4) - 1.2) / 0.92)
        brake_cmd = brake_damping * (1.6 + (2.05 * log10(-0.7 * js_inputs[brake_axis] + 1.4) - 1.2) / 0.92)

        throttle_cmd = max(0, min(1, throttle_cmd))
        brake_cmd = max(0, min(1, brake_cmd))

        self.control_state.set_steer(steer_cmd)
        self.control_state.set_throttle(throttle_cmd)
        self.control_state.set_brake(brake_cmd)

