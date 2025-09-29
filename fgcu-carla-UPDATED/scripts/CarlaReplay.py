import carla
import pygame
import numpy as np
import time
import math

import numpy as np
import math

def main():
    pygame.init()
    client = carla.Client('localhost', 2000)
    client.set_timeout(120.0)
    world = client.get_world()

    recording_file = r"C:\carla_env\fgcu-carla-UPDATED\scripts\recordings\scenario_20250926_162532.rec"

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

    bp_name = ghost_sensor.type_id
    blueprint_library = world.get_blueprint_library()
    camera_bp = blueprint_library.find(bp_name)

    # Get the ghost sensor's transform relative to the vehicle
    sensor_tf_world = ghost_sensor.get_transform()
    vehicle_tf_world = vehicle.get_transform()

    # Compute the relative transform
    relative_location = sensor_tf_world.location - vehicle_tf_world.location
    sensor_rot = sensor_tf_world.rotation
    vehicle_rot = vehicle_tf_world.rotation

    relative_rotation = carla.Rotation(
        pitch=sensor_rot.pitch - vehicle_rot.pitch,
        yaw=sensor_rot.yaw - vehicle_rot.yaw,
        roll=sensor_rot.roll - vehicle_rot.roll
    )

    relative_rotation = carla.Rotation(
        pitch=0,
        yaw=0,
        roll=0
    )

    relative_tf = carla.Transform(relative_location, relative_rotation)

    ghost_sensor.destroy()

    camera = world.spawn_actor(camera_bp, relative_tf, attach_to=vehicle)


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
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            time.sleep(0.01)
    finally:
        camera.stop()
        pygame.quit()

if __name__ == "__main__":
    main()
