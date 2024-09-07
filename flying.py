import carla
import pygame
import sys
import time

# Initialize pygame
pygame.init()

# Screen dimensions for Pygame
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('CARLA Fly Around to Get Coordinates')

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Font for displaying text
font = pygame.font.Font(None, 36)

# CARLA setup
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)  # Increase timeout to 10 seconds

# World and spectator setup
try:
    world = client.get_world()
    spectator = world.get_spectator()
except RuntimeError as e:
    print(f"Error connecting to CARLA: {e}")
    sys.exit(1)

def draw_coordinates(screen, font, location):
    """Display the current coordinates on the screen."""
    coords_text = f"X: {location.x:.2f}, Y: {location.y:.2f}, Z: {location.z:.2f}"
    text = font.render(coords_text, True, WHITE)
    screen.blit(text, (20, 20))

def main():
    clock = pygame.time.Clock()

    running = True
    while running:
        screen.fill(BLACK)

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Get the spectator (camera) transform to get the coordinates
        transform = spectator.get_transform()
        location = transform.location

        # Fly controls (move spectator with W, A, S, D and Q, E for vertical movement)
        if keys[pygame.K_w]:
            spectator.set_transform(carla.Transform(location + carla.Location(x=1)))
        if keys[pygame.K_s]:
            spectator.set_transform(carla.Transform(location + carla.Location(x=-1)))
        if keys[pygame.K_a]:
            spectator.set_transform(carla.Transform(location + carla.Location(y=-1)))
        if keys[pygame.K_d]:
            spectator.set_transform(carla.Transform(location + carla.Location(y=1)))
        if keys[pygame.K_q]:  # Move down
            spectator.set_transform(carla.Transform(location + carla.Location(z=-1)))
        if keys[pygame.K_e]:  # Move up
            spectator.set_transform(carla.Transform(location + carla.Location(z=1)))

        # Draw the coordinates on the screen
        draw_coordinates(screen, font, location)

        # Update display
        pygame.display.flip()

        # Limit to 60 FPS
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
