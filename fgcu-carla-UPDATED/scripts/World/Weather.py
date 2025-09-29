
import re
import carla

class WeatherManager:
    def __init__(self):
        self._weather_presets = self._find_weather_presets()
        self._weather_index = 0

    def _find_weather_presets(self):
        rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
        name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
        presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
        return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]

    def next_weather(self, world, hud, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        hud.notification(f'Weather: {preset[1]}')
        world.set_weather(preset[0])

    @property
    def current_preset(self):
        return self._weather_presets[self._weather_index]
