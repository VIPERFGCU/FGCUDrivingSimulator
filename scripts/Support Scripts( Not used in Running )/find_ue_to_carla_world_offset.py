import carla

client = carla.Client('localhost', 2000)
client.load_world("Town03")
world = client.get_world()
carla_map = world.get_map()

origin = carla_map.transform_to_geolocation(carla.Location(0, 0, 0))
print(origin)
