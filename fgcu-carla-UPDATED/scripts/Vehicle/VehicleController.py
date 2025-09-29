"""
    File: dual_control.py
    Author: Siang Chin
    Edited: 15/9/2025 10:37am

    This file is the main file that controls a Vehicle. It parses key events and 
    controls the car. Currently it only drives it.
"""

import carla
import pygame

from .VehicleSteering import VehicleControlState
from .InputMappingSettings import InputMapping
from .VehicleLights import VehicleLightsController

from math import tan, log10


class VehicleController:
    def __init__(self, player: carla.Vehicle, world, start_in_autopilot):
        self._autopilot_enabled = start_in_autopilot
        self._player = player

        if not isinstance(self._player, carla.Vehicle):
            raise NotImplementedError("The assigned object is not a vehicle")

        self._player.set_autopilot(self._autopilot_enabled)

        self.control_state = VehicleControlState()
        self.input_mapping = InputMapping(world.config_handler)
        self.input_handler = None
        self.lights_controller = VehicleLightsController(self._player)

        self.world = world
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        
        # keep track of pressed keys manually
        self._pressed_keys = {}

    def parse_events(self, clock, events):
        """
        Main input handler called every frame.
        Processes both keyboard and joystick events.
        """
        if not self._autopilot_enabled:
            for event in events:
                if event.type == pygame.QUIT:
                    return True
                elif event.type == pygame.JOYBUTTONDOWN:
                    self._handle_joystick_button(event)
                elif event.type == pygame.KEYDOWN:
                    self._pressed_keys[event.key] = True
                elif event.type == pygame.KEYUP:
                    self._pressed_keys[event.key] = False
                    self._handle_key(event)

            # continuous input (keys held down / joystick axes)
            milliseconds = clock.get_time()
            self.parse_keyboard_input(milliseconds)
            self.parse_joystick_input()

            # update lights after input
            self.lights_controller.update_lights(self.control_state)

        ### APPLY CONTROLS ###
        self._player.apply_control(self.control_state.get_control())

    # -------------------------
    # Keyboard input handling
    # -------------------------
    def parse_keyboard_input(self, milliseconds):
        keys = self._pressed_keys

        throttle = 1.0 if keys.get(pygame.K_UP) or keys.get(pygame.K_w) else 0.0
        self.control_state.set_throttle(throttle)

        steer_increment = 5e-4 * milliseconds
        if keys.get(pygame.K_LEFT) or keys.get(pygame.K_a):
            self.control_state.update_steering(-steer_increment)
        elif keys.get(pygame.K_RIGHT) or keys.get(pygame.K_d):
            self.control_state.update_steering(steer_increment)
        else:
            self.control_state.reset_steering()

        brake = 1.0 if keys.get(pygame.K_DOWN) or keys.get(pygame.K_s) else 0.0
        self.control_state.set_brake(brake)

        hand_brake = bool(keys.get(pygame.K_SPACE))
        self.control_state.set_hand_brake(hand_brake)


    # -------------------------
    # Joystick input handling
    # -------------------------
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

    # -------------------------
    # Button events
    # -------------------------
    def _handle_joystick_button(self, event):
        reverse_button = self.input_mapping.get_axis('reverse')
        handbrake_button = self.input_mapping.get_axis('handbrake')
        hide_hud_button = self.input_mapping.get_axis('hide_hud')
        toggle_headlights_button = self.input_mapping.get_axis('toggle_headlights')

        if reverse_button is not None and event.button == reverse_button:
            self.control_state.set_reverse(not self.control_state.get_reverse())
        elif handbrake_button is not None and event.button == handbrake_button:
            self.control_state.set_hand_brake(not self.control_state.get_hand_brake())
        elif hide_hud_button is not None and event.button == hide_hud_button:
            self.world.hud.toggle_info()
        elif toggle_headlights_button is not None and event.button == toggle_headlights_button:
            self.world.toggle_headlights()

    def _handle_key(self, event):
        keymap = self.input_mapping.key_mapping

        if keymap.get('reverse') and event.key == getattr(pygame, f'K_{keymap["reverse"].lower()}', None):
            self.control_state.set_reverse(not self.control_state.get_reverse())
        elif keymap.get('handbrake') and event.key == getattr(pygame, f'K_{keymap["handbrake"]}', None):
            self.control_state.set_hand_brake(not self.control_state.get_hand_brake())
        elif keymap.get('toggle_headlights') and event.key == getattr(pygame, f'K_{keymap["toggle_headlights"]}', None):
            self.world.toggle_headlights()

        if event.key == pygame.K_p:
            self._autopilot_enabled = not self._autopilot_enabled
            self._player.set_autopilot(self._autopilot_enabled)
        elif event.key == pygame.K_l:
            self.lights_controller.toggle_high_beam()
