
class World:
    def __init__(self, carla_world, actor_filter, config_handler):
        self.carla_world = carla_world
        # self._hud = hud
        self._actor_filter = actor_filter
        self.config_handler = config_handler

        # self.carla_world.on_tick(self._hud.on_world_tick)

        # self._hud.notification("Press 'H' or '?' for help.", seconds=4.0)

    def tick(self, clock):
        pass

    def render(self, display):
        # self.vehicle_manager.sensor_manager.render(display)
        # self._hud.render(display)
        pass

    def next_weather(self, reverse=False):
        self.weather_manager.next_weather(self.carla_world, self._hud, reverse=reverse)
