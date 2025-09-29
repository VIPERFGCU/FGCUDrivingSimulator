"""
    filename: VehicleSteering.py
    author: Siang Chin
    This file handles all settings present in the vehicle.
    @param _steer_cache is for smoothing keyboard steering
"""

import carla

class VehicleControlState:
    def __init__(self):
        self._control = carla.VehicleControl()
        self._control.manual_gear_shift = False # No manual steering
        self._steer_cache = 0.0

    def get_control(self):
        return self._control

    def set_throttle(self, value: float):
        self._control.throttle = max(0.0, min(1.0, value))

    def get_throttle(self) -> float:
        return self._control.throttle

    def set_brake(self, value: float):
        self._control.brake = max(0.0, min(1.0, value))

    def get_brake(self) -> float:
        return self._control.brake

    def set_steer(self, value: float):
        self._control.steer = max(-1.0, min(1.0, value))

    def get_steer(self) -> float:
        return self._control.steer

    def set_hand_brake(self, enabled: bool):
        self._control.hand_brake = enabled

    def get_hand_brake(self) -> bool:
        return self._control.hand_brake

    def set_gear(self, gear: int):
        self._control.gear = gear

    def get_gear(self) -> int:
        return self._control.gear

    def set_reverse(self, reverse: bool):
        self._control.reverse = reverse

    def get_reverse(self) -> bool:
        return self._control.reverse

    # Smooth Steering
    def update_steering(self, increment: float):
        self._steer_cache += increment
        self._steer_cache = max(-0.7, min(0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)

    def reset_steering(self):
        self._steer_cache = 0.0
        self._control.steer = 0.0
