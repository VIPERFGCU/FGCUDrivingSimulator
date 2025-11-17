import csv
import carla
import pygame
import numpy as np
import time
import math
import os
import glob
import re

def get_recording_duration(info_text):
    """Extract total duration (seconds) from show_recorder_file_info() output."""
    match = re.search(r"Duration:\s*([\d\.]+)\s*s", info_text)
    if match:
        return float(match.group(1))
    return None


def process_recording(client, recording_file):
    """Replay a CARLA .rec file and log vehicle position & speed to CSV."""
    print(f"\n=== Processing recording: {recording_file} ===\n")

    # Reload the world (ensures a clean start)
    print("Reloading world...")
    world = client.reload_world()
    world.wait_for_tick()
    time.sleep(1)

    pygame.init()

    # Get info and duration
    try:
        info_text = client.show_recorder_file_info(recording_file, show_all=False)
        print(info_text)
        duration = get_recording_duration(info_text)
        if duration:
            print(f"Recording duration detected: {duration:.2f} seconds")
        else:
            print("⚠️ Could not detect recording duration; defaulting to 60 seconds.")
            duration = 60.0
    except Exception as e:
        print(f"Error reading recording info: {e}")
        return

    # Start replay
    try:
        client.replay_file(recording_file, 0.0, 0.0, 0, True)
    except Exception as e:
        print(f"Error starting replay: {e}")
        return

    world.wait_for_tick()
    time.sleep(1)

    # Wait for a vehicle to spawn
    vehicle = None
    print("Waiting for vehicles to spawn from recording...")
    while vehicle is None:
        actors = world.get_actors().filter('vehicle.*')
        if actors:
            vehicle = actors[0]
            print(f"Vehicle found! ID: {vehicle.id}")
        else:
            time.sleep(0.1)

    # Wait for ghost RGB camera
    ghost_sensor = None
    print("Waiting for ghost RGB camera sensor to appear...")
    while ghost_sensor is None:
        sensors = world.get_actors().filter('sensor.camera.rgb')
        if sensors:
            ghost_sensor = sensors[0]
            print(f"Ghost camera found! ID: {ghost_sensor.id}")
        else:
            time.sleep(0.1)

    # Recreate camera on vehicle
    bp_name = ghost_sensor.type_id
    blueprint_library = world.get_blueprint_library()
    camera_bp = blueprint_library.find(bp_name)
    ghost_sensor.destroy()

    camera = world.spawn_actor(
        camera_bp,
        carla.Transform(
            carla.Location(x=-0.1, y=-0.35, z=1.2),
            carla.Rotation(pitch=-10.0, yaw=0.0, roll=0.0)
        ),
        attach_to=vehicle
    )

    width = int(camera.attributes['image_size_x'])
    height = int(camera.attributes['image_size_y'])
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(f"CARLA Replay Viewer - {os.path.basename(recording_file)}")

    def show_camera(image):
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = array.reshape((image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        screen.blit(surface, (0, 0))
        pygame.display.flip()

    camera.listen(show_camera)

    # Output CSV
    output_dir = os.path.dirname(recording_file)
    base_name = os.path.splitext(os.path.basename(recording_file))[0]
    csv_path = os.path.join(output_dir, f"{base_name}_vehicle_positions.csv")
    print(f"Logging vehicle data to: {csv_path}")

    prev_loc, prev_time = None, None
    last_output_time = -1.0
    start = 0
    running = True

    with open(csv_path, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["time", "x", "y", "z", "speed_mph"])

        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                snapshot = world.wait_for_tick()
                if snapshot is None:
                    continue

                sim_time = snapshot.timestamp.elapsed_seconds
                if start == 0:
                    start = sim_time

                elapsed = sim_time - start
                if elapsed >= duration:
                    print(f"Recording finished after {elapsed:.2f}s.")
                    break  # ✅ Stop when recording ends

                # Log vehicle position each simulated second
                if sim_time - last_output_time >= 1.0:
                    if vehicle and vehicle.is_alive:
                        loc = vehicle.get_transform().location

                        # Estimate speed
                        speed_mph = 0.0
                        if prev_loc and prev_time:
                            dx = loc.x - prev_loc.x
                            dy = loc.y - prev_loc.y
                            dz = loc.z - prev_loc.z
                            dist_m = math.sqrt(dx**2 + dy**2 + dz**2)
                            dt = sim_time - prev_time
                            if dt > 0:
                                speed_mph = (dist_m / dt) * 2.23694

                        prev_loc, prev_time = carla.Location(loc.x, loc.y, loc.z), sim_time

                        writer.writerow([
                            f"{elapsed:.2f}",
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
            print(f"✅ Finished processing {recording_file}\n")


def main():
    rec_dir = r"C:\carla_env\FGCUDrivingSimulator\data\DrV_20251110_150849"

    # Find all .rec files recursively
    rec_files = glob.glob(os.path.join(rec_dir, "**", "*.rec"), recursive=True)
    if not rec_files:
        print(f"No .rec files found in {rec_dir}")
        return

    print(f"Found {len(rec_files)} .rec files to process.\n")

    # Connect to CARLA once, reuse client
    client = carla.Client('localhost', 2000)
    client.set_timeout(100.0)

    for rec_file in rec_files:
        try:
            process_recording(client, rec_file)
        except Exception as e:
            print(f"⚠️ Error processing {rec_file}: {e}")
            continue


if __name__ == "__main__":
    main()
