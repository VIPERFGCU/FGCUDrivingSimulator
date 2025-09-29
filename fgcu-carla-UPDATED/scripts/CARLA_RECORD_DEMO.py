import glob
import os
import sys
import argparse
import math
import random
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
from Camera.Camera import CameraManager
from Hud.Hud import HUD
from Setup.ConfigHandler import ConfigHandler
from World.World import World
from Vehicle.Vehicle import Vehicle
from Trial.DataCollector import ScenarioRecorder
from Trial.DataCollectorInternal import CarlaScenarioRecorder

##########################################
CARLA_SERVER_FPS = 60.0 # Make sure this is a float for fps calculations
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

        # Get current settings
        settings = world.carla_world.get_settings()

        # Real-time mode
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 1.0 / CARLA_SERVER_FPS  # ~0.0167s
        world.carla_world.apply_settings(settings)


        # --- clocks ---
        client_clock = pygame.time.Clock()

        # HUD update
        # world.carla_world.on_tick(hud.on_world_tick)

        running = True
        client_clock = pygame.time.Clock()

        rec = CarlaScenarioRecorder(vehicle.get_player(), client)
        rec.start()

        while running:
            # Limit frame rate to 60 FPS

            # Step the simulation (advances physics one tick)
            world.carla_world.tick()
            world_snapshot = world.carla_world.get_snapshot()
            hud.on_world_tick(world_snapshot)
            # rec.record_frame()    <-- You only need this if doing internal checking.

            # Handle input/events
            events = pygame.event.get()
            vehicle.tick(client_clock, events)

            # Update + render
            hud.tick(vehicle, world, client_clock)
            vehicle.render(display)
            hud.render(display)
            pygame.display.flip()

            for event in events:
                if event.type == pygame.KEYUP and event.key == pygame.K_1:
                    rec.stop()
            client_clock.tick_busy_loop(CARLA_SERVER_FPS)

    finally:
        if vehicle is not None:
            # world.destroy()
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