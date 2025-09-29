"""
    filename: HelpText.py
    Author: Siang Chin
    This file renders help text to the screen.
    All help text is created here
"""

import pygame

class HelpText(object):
    def __init__(self, font, width, height):
        help_lines = [
            "Welcome to CARLA manual control with steering wheel Logitech G29.",
            "To drive start by pressing the brake pedal.",
            "Change your wheel_config.ini according to your steering wheel.",
            "To find out the values of your steering wheel use jstest-gtk in Ubuntu.",
            "",
            "Controls:",
            "  - Arrow keys or WASD: Control the vehicle",
            "  - Space: Hand brake",
            "  - Backspace: Restart",
            "  - F1: Toggle info",
            "  - H or /?: Toggle help",
            "  - Tab: Change camera",
            "  - C: Change weather",
            "  - Backquote: Next sensor",
            "  - R: Toggle recording",
            "  - Q: Toggle reverse gear",
            "  - M: Toggle manual transmission",
            "  - , or .: Change gear in manual transmission",
            "  - P: Toggle autopilot",
            "  - L: Toggle vehicle lights",
            "  - J: Toggle headlights"
        ]

        self.font = font
        self.dim = (680, len(help_lines) * 22 + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill((0, 0, 0, 0))

        for n, line in enumerate(help_lines):
            text_texture = self.font.render(line, True, (255, 255, 255))
            self.surface.blit(text_texture, (22, n * 22))
        self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        self._render = not self._render

    def render(self, display):
        if self._render:
            display.blit(self.surface, self.pos)