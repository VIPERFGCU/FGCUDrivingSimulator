import carla
import os
import time
import random

# Define the base output directory
BASE_OUTPUT_DIR = r"C:\carla_env\fgcu-carla\scripts\output"

def log_vehicle_state(vehicle, weather_level):
    """Log vehicle position, rotation, and velocity."""
    output_folder = os.path.join(BASE_OUTPUT_DIR, f'vehicle_state/level_{weather_level}')
    os.makedirs(output_folder, exist_ok=True)

    state = vehicle.get_transform()
    velocity = vehicle.get_velocity()
    file_path = os.path.join(output_folder, f'vehicle_state_{time.time()}.txt')
    with open(file_path, 'w') as f:
        f.write(f"Position: {state.location}, Rotation: {state.rotation}, Velocity: {velocity}\n")
    print(f"Logged vehicle state for level {weather_level} to {file_path}")


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
    # Connect to CARLA
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)

    # Load Town03
    world = client.load_world('Town03')

    # Define weather levels and transitions
    weather_conditions = [
        carla.WeatherParameters.ClearNoon,
        carla.WeatherParameters.SoftRainNoon,
        carla.WeatherParameters.MidRainyNoon,
        carla.WeatherParameters.HardRainNoon,
        carla.WeatherParameters.WetCloudyNoon,
        carla.WeatherParameters.HardRainNoon
    ]

    # Spawn ego vehicle
    blueprint_library = world.get_blueprint_library()
    vehicle_bp = blueprint_library.filter('vehicle.*')[0]
    spawn_point = random.choice(world.get_map().get_spawn_points())
    vehicle = world.spawn_actor(vehicle_bp, spawn_point)

    # Enable autopilot
    vehicle.set_autopilot(True)

    try:
        total_logged = 0  # Counter for total logs
        for idx, weather in enumerate(weather_conditions):
            print(f"Setting weather level {idx}")

            # Gradual weather transition
            if idx > 0:
                gradually_change_weather(world, weather_conditions[idx - 1], weather, 10)

            # Apply current weather
            world.set_weather(weather)

            # Collect vehicle state data for an extended duration
            duration = 60  # Increased to 60 seconds per weather condition
            start_time = time.time()
            while time.time() - start_time < duration:
                log_vehicle_state(vehicle, idx)
                total_logged += 1
                if total_logged >= 1000:  # Stop when enough data is collected
                    print(f"Collected {total_logged} logs. Stopping.")
                    return
                time.sleep(0.5)  # Increased logging frequency

    except KeyboardInterrupt:
        print("Data collection interrupted by user.")
    finally:
        vehicle.destroy()
        print("Vehicle destroyed.")

if __name__ == "__main__":
    main()
