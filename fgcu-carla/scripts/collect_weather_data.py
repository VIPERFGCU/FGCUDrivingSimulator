import carla
import os
import pygame
import numpy as np
import time
import random

def save_camera_image(image, weather_level):
    """Save camera image to disk."""
    output_folder = f'output/camera/level_{weather_level}'
    os.makedirs(output_folder, exist_ok=True)
    image.save_to_disk(f'{output_folder}/frame_{image.frame}.png')

def save_radar_data(radar_data, weather_level):
    """Save radar data to a text file."""
    output_folder = f'output/radar/level_{weather_level}'
    os.makedirs(output_folder, exist_ok=True)
    with open(f'{output_folder}/frame_{radar_data.frame}.txt', 'w') as f:
        for detection in radar_data:
            f.write(f"{detection.depth}, {detection.azimuth}, {detection.altitude}, {detection.velocity}\n")

def save_lidar_data(lidar_data, weather_level):
    """Save LiDAR data to a text file."""
    output_folder = f'output/lidar/level_{weather_level}'
    os.makedirs(output_folder, exist_ok=True)
    lidar_points = lidar_data.raw_data
    with open(f'{output_folder}/frame_{lidar_data.frame}.txt', 'w') as f:
        f.write(str(list(lidar_points)))

def log_vehicle_state(vehicle, weather_level):
    """Log vehicle position, rotation, and velocity."""
    state = vehicle.get_transform()
    velocity = vehicle.get_velocity()
    output_folder = f'output/vehicle_state/level_{weather_level}'
    os.makedirs(output_folder, exist_ok=True)
    with open(f'{output_folder}/vehicle_state_{time.time()}.txt', 'w') as f:
        f.write(f"Position: {state.location}, Rotation: {state.rotation}, Velocity: {velocity}\n")

def camera_callback(image, weather_level, display_surface):
    """Handle camera feed, save image, and display POV."""
    # Convert CARLA image to numpy array
    array = np.frombuffer(image.raw_data, dtype=np.uint8)
    array = array.reshape((image.height, image.width, 4))  # BGRA format

    # Save image
    save_camera_image(image, weather_level)

    # Convert BGRA to RGB for Pygame and display
    surface = pygame.surfarray.make_surface(array[:, :, :3])
    display_surface.blit(pygame.transform.rotate(surface, -90), (0, 0))
    pygame.display.flip()

def gradually_change_weather(world, start_weather, end_weather, duration):
    """Gradually transition weather over a specified duration."""
    steps = int(duration / 0.5)
    for step in range(steps):
        transition_weather = carla.WeatherParameters(
            cloudiness=start_weather.cloudiness + step * (end_weather.cloudiness - start_weather.cloudiness) / steps,
            precipitation=start_weather.precipitation + step * (end_weather.precipitation - start_weather.precipitation) / steps,
            precipitation_deposits=start_weather.precipitation_deposits + step * (end_weather.precipitation_deposits - start_weather.precipitation_deposits) / steps,
            wind_intensity=start_weather.wind_intensity + step * (end_weather.wind_intensity - start_weather.wind_intensity) / steps,
        )
        world.set_weather(transition_weather)
        time.sleep(0.5)

def main():
    # Initialize Pygame for rendering
    pygame.init()
    display_width, display_height = 1280, 720
    display_surface = pygame.display.set_mode((display_width, display_height))
    pygame.display.set_caption("Ego Vehicle Camera Feed")

    # Connect to CARLA
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)

    # Load Town03
    world = client.load_world('Town03')

    # Define weather levels and transitions
    weather_conditions = [
        carla.WeatherParameters.ClearNoon,          # Level 0
        carla.WeatherParameters.SoftRainNoon,       # Level 1
        carla.WeatherParameters.MidRainyNoon,       # Level 2
        carla.WeatherParameters.HardRainNoon,       # Level 3
        carla.WeatherParameters.WetCloudyNoon,      # Level 4
        carla.WeatherParameters.HardRainNoon        # Level 5 (extreme)
    ]

    # Spawn the ego vehicle
    blueprint_library = world.get_blueprint_library()
    vehicle_bp = blueprint_library.filter('vehicle.*')[0]
    spawn_point = random.choice(world.get_map().get_spawn_points())
    vehicle = world.spawn_actor(vehicle_bp, spawn_point)

    # Enable autopilot for driving
    vehicle.set_autopilot(True)

    # Attach camera
    camera_bp = blueprint_library.find('sensor.camera.rgb')
    camera_bp.set_attribute('image_size_x', f'{display_width}')
    camera_bp.set_attribute('image_size_y', f'{display_height}')
    camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))  # Front-facing
    camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

    # Attach radar
    radar_bp = blueprint_library.find('sensor.other.radar')
    radar_transform = carla.Transform(carla.Location(x=1.5, z=1.0))  # Front-mounted
    radar = world.spawn_actor(radar_bp, radar_transform, attach_to=vehicle)

    # Attach LiDAR
    lidar_bp = blueprint_library.find('sensor.lidar.ray_cast')
    lidar_transform = carla.Transform(carla.Location(x=1.5, z=2.4))  # Roof-mounted
    lidar = world.spawn_actor(lidar_bp, lidar_transform, attach_to=vehicle)

    try:
        # Loop through each weather condition
        for idx, weather in enumerate(weather_conditions):
            print(f"Setting weather level {idx}")
            
            # Gradual weather transition (optional for transitions)
            if idx > 0:
                gradually_change_weather(world, weather_conditions[idx - 1], weather, 10)

            # Apply current weather level
            world.set_weather(weather)

            # Start camera data collection and display
            camera.listen(lambda image: camera_callback(image, idx, display_surface))
            radar.listen(lambda radar_data: save_radar_data(radar_data, idx))
            lidar.listen(lambda lidar_data: save_lidar_data(lidar_data, idx))

            # Collect data for 20 seconds
            start_time = time.time()
            while time.time() - start_time < 20:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise KeyboardInterrupt
                log_vehicle_state(vehicle, idx)

            # Stop listeners before switching weather
            camera.stop()
            radar.stop()
            lidar.stop()

    except KeyboardInterrupt:
        print("Data collection interrupted by user.")
    finally:
        # Clean up actors
        camera.destroy()
        radar.destroy()
        lidar.destroy()
        vehicle.destroy()
        pygame.quit()
        print("Actors destroyed.")

if __name__ == "__main__":
    main()
