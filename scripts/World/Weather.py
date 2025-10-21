
import re
import carla

from Hud.Hud import HUD

class WeatherManager:
    def __init__(self, world: carla.World, hud : HUD):
        self.world = world
        self.hud = hud

        # Weather settings. Pass the key into set_weather to change the weather
        self._weather_presets = {
            "ClearNoon": carla.WeatherParameters.ClearNoon,
            "ClearSunset": carla.WeatherParameters.ClearSunset,
            "CloudyNoon": carla.WeatherParameters.CloudyNoon,
            "CloudySunset": carla.WeatherParameters.CloudySunset,
            "WetNoon": carla.WeatherParameters.WetNoon,
            "WetSunset": carla.WeatherParameters.WetSunset,
            "MidRainyNoon": carla.WeatherParameters.MidRainyNoon,
            "MidRainSunset": carla.WeatherParameters.MidRainSunset,
            "HardRainNoon": carla.WeatherParameters.HardRainNoon,
            "HardRainSunset": carla.WeatherParameters.HardRainSunset,
            "SoftRainNoon": carla.WeatherParameters.SoftRainNoon,
            "SoftRainSunset": carla.WeatherParameters.SoftRainSunset,
            "ClearNight": carla.WeatherParameters.ClearNight,
            "CloudyNight": carla.WeatherParameters.CloudyNight,
            "WetNight": carla.WeatherParameters.WetNight,
            "MidRainyNight": carla.WeatherParameters.MidRainyNight,
            "HardRainNight": carla.WeatherParameters.HardRainNight,
            "SoftRainNight": carla.WeatherParameters.SoftRainNight
        }

    def set_weather(self, weather_tag: str):
        """
        Set CARLA weather by tag. Example: set_weather("ClearNoon")
        """
        preset = self._weather_presets.get(weather_tag)
        if not preset:
            raise ValueError(f"Invalid weather tag '{weather_tag}'. Valid options: {list(self._weather_presets.keys())}")
        self.world.set_weather(preset)
        
        self.hud.notification(f"Current Weather: {weather_tag}", 2)
        print(f"Current Weather: {weather_tag}")
