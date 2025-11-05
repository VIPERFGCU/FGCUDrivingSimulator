import csv
import carla
import pygame
import numpy as np
import time
import math
import os

import numpy as np
import math

def main():
    pygame.init()
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    recording_file = r"C:\carla_env\FGCUDrivingSimulator\data\TestAgain_20251014_173620\ClearNoon.rec"

    print(recording_file)
    # Show info about the recording
    print(client.show_recorder_file_info(recording_file, show_all=False))

    # Start replay without following any actor
    client.replay_file(recording_file, 0.0, 0.0, 0, True)
    
    world.wait_for_tick()
    time.sleep(1)

    # Wait for a vehicle from the recording
    vehicle = None
    print("Waiting for vehicles to spawn from recording...")
    while vehicle is None:
        actors = world.get_actors().filter('vehicle.*')
        if actors:
            vehicle = actors[0]
            print(f"Vehicle found! ID: {vehicle.id}")
        else:
            time.sleep(0.1)

    # Find a ghost RGB camera sensor
    ghost_sensor = None
    print("Waiting for ghost RGB camera sensor to appear...")
    while ghost_sensor is None:
        sensors = world.get_actors().filter('sensor.camera.rgb')
        if sensors:
            ghost_sensor = sensors[0]
            print(f"Ghost camera found! ID: {ghost_sensor.id}")
        else:
            time.sleep(0.1)

    # Load the new camera object
    bp_name = ghost_sensor.type_id
    blueprint_library = world.get_blueprint_library()
    camera_bp = blueprint_library.find(bp_name)

    ghost_sensor.destroy()

    # Spawn the new camera
    camera = world.spawn_actor(camera_bp, carla.Transform(carla.Location(x=-0.1, y=-0.35, z=1.2), carla.Rotation(pitch=-10.0, yaw=0.0, roll=0.0)), attach_to=vehicle)


    # Setup Pygame window
    width = int(camera.attributes['image_size_x'])
    height = int(camera.attributes['image_size_y'])
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("CARLA Recording Camera Viewer")

    # Display camera feed
    def show_camera(image):
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = array.reshape((image.height, image.width, 4))
        array = array[:, :, :3]  # Drop alpha channel
        array = array[:, :, ::-1]  # Convert BGRA -> RGB
        surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        screen.blit(surface, (0, 0))
        pygame.display.flip()

    camera.listen(show_camera)

    # Run until user quits
    running = True
    last_output_time = -1.0  # seconds


    output_dir = os.path.dirname(recording_file)
    csv_path = os.path.join(output_dir, "vehicle_positions_mph_ClearNoon.csv")
    print(f"Logging vehicle data to: {csv_path}")

    # Initialize previous location/time for speed estimation (avoid "referenced before assignment")
    prev_loc = None      # will hold a carla.Location (or tuple)
    prev_time = None     # will hold previous sim_time (float)

    with open(csv_path, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["time", "x", "y", "z", "speed_mph"])

        running = True
        last_output_time = -1.0

        try:
            start = 0
            while running:
                # Handle window quit
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                # Sync with replay time
                snapshot = world.wait_for_tick()
                if snapshot is None:
                    # in rare cases wait_for_tick can return None; continue safely
                    continue
                sim_time = snapshot.timestamp.elapsed_seconds
                if start == 0:
                    start = sim_time
                # Log every simulated second
                if sim_time - last_output_time >= 1.0:
                    if vehicle is not None and vehicle.is_alive:
                        transform = vehicle.get_transform()
                        loc = transform.location

                        # Compute estimated speed (since get_velocity() = 0 in replay)
                        speed_mph = 0.0
                        if (prev_loc is not None) and (prev_time is not None):
                            dx = loc.x - prev_loc.x
                            dy = loc.y - prev_loc.y
                            dz = loc.z - prev_loc.z
                            dist_m = math.sqrt(dx*dx + dy*dy + dz*dz)
                            dt = sim_time - prev_time
                            if dt > 0:
                                speed_m_s = dist_m / dt
                                speed_mph = speed_m_s * 2.23694
                        else:
                            # First measurement: speed unknown -> 0.0
                            speed_mph = 0.0

                        # Update prev_loc and prev_time for next interval
                        prev_loc = carla.Location(loc.x, loc.y, loc.z)
                        prev_time = sim_time

                        # Write to CSV (x,y,z in meters, speed in mph)
                        writer.writerow([
                            f"{(sim_time - start):.2f}",
                            f"{loc.x:.2f}",
                            f"{loc.y:.2f}",
                            f"{loc.z:.2f}",
                            f"{speed_mph:.2f}"
                        ])
                        csvfile.flush()

                        print(f"[t={sim_time:8.2f}s] "
                              f"x={loc.x:8.2f}, y={loc.y:8.2f}, z={loc.z:6.2f}, "
                              f"speed={speed_mph:6.2f} mph")

                    last_output_time = sim_time

        finally:
            camera.stop()
            pygame.quit()

if __name__ == "__main__":
    main()
