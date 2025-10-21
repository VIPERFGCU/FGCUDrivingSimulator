import glob
import os
import sys
import argparse
import threading

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

try:
    import pygame
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

####        Internal Imports           ###
from Trial.TrialStateMachine import Trial
from Hud.Hud import HUD
from Setup.ConfigHandler import ConfigHandler
from World.World import World
from Vehicle.Vehicle import Vehicle
from Trial.TrialManager import TrialManager
from World.Weather import WeatherManager

##########################################
CARLA_SERVER_FPS = 30.0 # Make sure this is a float for fps calculations
def game_loop(args):
    pygame.init()
    pygame.font.init()
    world = None
    vehicle = None

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(10)

        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        # Load the specified town
        town_name = args.town if args.town else 'Town03'
        client.load_world(town_name)


        # Create a clock for managing frame rate
        client_clock = pygame.time.Clock()

        config_handler = ConfigHandler()
        config_handler.load_config()

        world = World(client.get_world(), args.filter, config_handler)
        hud = HUD(args.width, args.height, config_handler, client_clock)
        vehicle = Vehicle(world, config_handler, args.filter, hud)
        weather_manager = WeatherManager(world.carla_world, hud)

        trial_manager = TrialManager(vehicle, config_handler, client, weather_manager)

        # Get current settings
        settings = world.carla_world.get_settings()

        # Use synchronous mode with fixed timestep
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 1.0 / CARLA_SERVER_FPS
        world.carla_world.apply_settings(settings)

        # Initialize client clock before starting the thread
        running = True
        latest_snapshot = None
        new_snapshot_event = threading.Event()

        def syncronous_world_ticker():
            """Tick CARLA in a separate thread and notify main loop when a new snapshot is ready."""
            global latest_snapshot
            while running:
                world.carla_world.tick()
                snapshot = world.carla_world.get_snapshot()
                latest_snapshot = snapshot

                # Notify main loop a new snapshot is ready
                new_snapshot_event.set()


        client_clock = pygame.time.Clock()

        # Start CARLA ticking thread
        my_thread = threading.Thread(target=syncronous_world_ticker, daemon=True)
        my_thread.start()

        while running:
            # Wait for a new snapshot from the ticker thread
            new_snapshot_event.wait()
            new_snapshot_event.clear()

            world_snapshot = latest_snapshot
            if world_snapshot:
                hud.on_world_tick(world_snapshot)

            # Handle input/events
            events = pygame.event.get()
            if not trial_manager.trial_started or (
                trial_manager.current_trial.current_state == Trial.STATE.UNKNOWN or
                trial_manager.current_trial.current_state == Trial.STATE.RUNNING
            ):
                vehicle.tick(client_clock, events)

            # Update and render
            hud.tick(vehicle, world, client_clock)
            vehicle.render(display)
            trial_manager.tick(display, events)

            if not trial_manager.trial_started:
                hud.render(display)

            pygame.display.flip()

            for event in events:
                if event.type == pygame.KEYUP and event.key == pygame.K_1:
                    trial_manager.start_trials()

            client_clock.tick(1000) # Go as fast as possible so it is always waiting on Carla

            # Optional: throttle client-side rendering (doesn't affect simulation timing)
            # client_clock.tick(CARLA_SERVER_FPS)


    finally:
        if vehicle is not None:
            # world.destroy()
            # thread1.join()
            vehicle.destroy()

        pygame.quit()


def main():
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '--town',
        metavar='TOWN',
        default='Town03',
        help='Specify which town to load (default: "Town03")')
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    try:
        game_loop(args)
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':
    main()