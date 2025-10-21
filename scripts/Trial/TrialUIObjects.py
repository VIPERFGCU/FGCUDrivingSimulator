"""
    THIS FILE IS NOT INDICITAVE OF THE DATA THAT WILL BE ANALYZED. IT IS TO PROVIDE TESTERS VISUAL FEEDBACK OF THEIR ACTIONS
"""

import pygame

class UI:
    @staticmethod
    def render_start_screen(display):
        font = pygame.font.Font(None, 36)
        text_surface = font.render("Press Enter to Start Run", True, (255, 255, 255))
        text_surface.set_alpha(200)
        background = pygame.Surface((display.get_width(), display.get_height()))
        background.fill((0, 0, 0))
        background.set_alpha(150)
        display.blit(background, (0, 0))
        display.blit(text_surface, (display.get_width() // 2 - text_surface.get_width() // 2, display.get_height() // 2 - text_surface.get_height() // 2))

    @staticmethod
    def render_user_prompt_screen(display, current_text):
        font = pygame.font.Font(None, 36)
        text_surface = font.render("Enter Name to Continue. Press Enter to complete input.", True, (255, 255, 255))
        text_surface.set_alpha(200)
        background = pygame.Surface((display.get_width(), display.get_height()))
        background.fill((0, 0, 0))
        background.set_alpha(150)
        display.blit(background, (0, 0))
        display.blit(text_surface, (display.get_width() // 2 - text_surface.get_width() // 2, display.get_height() // 2 - text_surface.get_height() // 2))

        # Draw the text box for username
        font = pygame.font.Font(None, 32)
        input_box = pygame.Rect(640 - 100, 360 + 50, 200, 32)
        add_button = pygame.Rect(input_box.x + 210, input_box.y, 80, 32)
        # dropdown_rect = pygame.Rect(640 - 100, 360 + 82, 200, len(self.user_names) * 32)

        pygame.draw.rect(display, (255, 255, 255), input_box, 0)
        pygame.draw.rect(display, (0, 0, 0), input_box, 2)
        pygame.draw.rect(display, (0, 0, 0), add_button, 2)

        text_color = (0, 0, 0)
        name_surface = font.render(current_text, True, text_color)    # Update based on user_name
        display.blit(name_surface, (input_box.x + 5, input_box.y + 5))

        add_text = font.render("Add", True, (0, 0, 0))
        display.blit(add_text, (add_button.x + 5, add_button.y + 5))

        # Draw dropdown list
        # if self.dropdown_open:
        #     pygame.draw.rect(display, (255, 255, 255), dropdown_rect, 0)
        #     pygame.draw.rect(display, (0, 0, 0), dropdown_rect, 2)
        #     for i, name in enumerate(self.user_names):
        #         name_surface = font.render(name, True, (0, 0, 0))
        #         display.blit(name_surface, (dropdown_rect.x + 5, dropdown_rect.y + 5 + i * 32))

    @staticmethod
    def render_count_down_screen(display, remaining_time):
        font = pygame.font.Font(None, 72)
        countdown_text = font.render(str(remaining_time), True, (255, 255, 255))
        text_rect = countdown_text.get_rect()
        text_rect.center = (display.get_width() // 2, display.get_height() // 2)

        overlay = pygame.Surface((display.get_width(), display.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))    # Tranparent background

        display.blit(overlay, (0, 0))
        display.blit(countdown_text, text_rect)

    @staticmethod
    def render_speed(display, current_speed):
        font = pygame.font.Font(None, 36)

        speed_text = f"Speed: {int(round(current_speed))} mph"
        speed_surface = font.render(speed_text, True, (255, 255, 255))
        
        # Move speed display HIGHER above the steering wheel
        display.blit(speed_surface, (display.get_width() // 2 - speed_surface.get_width() // 2, display.get_height() - 400))

    @staticmethod
    def render_speed_warning(display):
        font = pygame.font.Font(None, 36)

        warning_text = "You are exceeding the speed limit!"
        warning_surface = font.render(warning_text, True, (255, 0, 0))
        display.blit(warning_surface, (display.get_width() // 2 - warning_surface.get_width() // 2, display.get_height() // 2 - warning_surface.get_height() // 2))

    @staticmethod
    def render_results(display, total_time):
        overlay = pygame.Surface((display.get_width(), display.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))    # Tranparent background
        display.blit(overlay, (0, 0))

        font = pygame.font.Font(None, 36)
        text = f"Results!\n total time: {total_time}"
        text_surface = font.render(text, True, (255, 255, 255))
        display.blit(text_surface, (display.get_width() // 2 - text_surface.get_width() // 2, display.get_height() // 2 - text_surface.get_height() // 2))