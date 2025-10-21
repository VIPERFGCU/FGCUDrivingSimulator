"""
    VehicleLights.py
    Setup 
"""
import carla
from .VehicleSteering import VehicleControlState

class VehicleLightsController:
    def __init__(self, vehicle : carla.Vehicle):
        self._vehicle = vehicle

    def update_lights(self, control_state: VehicleControlState):
        brake_light = control_state.get_brake() > 0.0
        reverse_light = control_state.get_gear() < 0
        self._set_brake_light(brake_light)
        self._set_reverse_light(reverse_light)
    
    def toggle_headlights(self):
        light_state = self._vehicle.get_light_state()
        current_lights = carla.VehicleLightState.NONE

        if not light_state & carla.VehicleLightState.LowBeam:
            current_lights |= carla.VehicleLightState.LowBeam
        else:
            current_lights = carla.VehicleLightState.NONE  # turn off

        self._vehicle.set_light_state(carla.VehicleLightState(current_lights))


    def toggle_high_beam(self):
        light_state = self._vehicle.get_light_state()
        if light_state & carla.VehicleLightState.HighBeam:
            new_state = light_state & ~carla.VehicleLightState.HighBeam
        else:
            new_state = light_state | carla.VehicleLightState.HighBeam
        self._vehicle.set_light_state(carla.VehicleLightState(new_state))
    
    def _set_brake_light(self, enabled: bool):
        """Enable or disable the brake lights for a vehicle without affecting other lights."""
        current = self._vehicle.get_light_state()
        if enabled:
            new_state = current | carla.VehicleLightState.Brake
        else:
            new_state = current & ~carla.VehicleLightState.Brake
        self._vehicle.set_light_state(carla.VehicleLightState(new_state))

    def _set_reverse_light(self, enabled: bool):
        """Enable or disable the reverse lights for a vehicle without affecting other lights."""
        current = self._vehicle.get_light_state()
        if enabled:
            new_state = current | carla.VehicleLightState.Reverse
        else:
            new_state = current & ~carla.VehicleLightState.Reverse
        self._vehicle.set_light_state(carla.VehicleLightState(new_state))
