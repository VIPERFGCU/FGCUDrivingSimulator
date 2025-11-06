import os
import carla

from Setup.ConfigHandler import ConfigHandler
from Trial.TrialStateMachine import Trial
from Vehicle.Vehicle import Vehicle
from World.Weather import WeatherManager


class TrialManager:
    def __init__(self, vehicle : Vehicle, config_handler : ConfigHandler, client : carla.Client, weather : WeatherManager):
        self.TRIAL_NUM = 8  # A constant
        self._vehicle = vehicle
        self.weather_manager = weather
        self.client = client

        # Trial Settings
        self._trial_settings = config_handler.load_config()[2]
        os.makedirs(self._trial_settings["data_save_location"], exist_ok=True)  # Make the main save folder if it doesn't already exist
        self.weather_list = [    # Each index refers to the loop - 1( starts from 0)
            "ClearNoon",
            "ClearSunset",
            "HardRainNoon",
            "CloudyNoon",
            "ClearNight",
            "HardRainNight",
            "CloudyNight",
            "Default"   # For the 8th trial
        ]
        
    
        #
        self.trial_started = False  # Changed in start_trials
        self.current_loop : int = -1    # Incremeted to 0 when next_trial is called
        self.current_trial : Trial = None

    def start_trials(self):
        if not self.trial_started:
            self.trial_started = True
            self.next_trial()
        
    
    # Start the next trial. Based off the current loop( increments by 1 )
    def next_trial(self):
        self.current_loop += 1
        if self.current_loop >= self.TRIAL_NUM:
            self.trial_started = False
            self.current_trial = None
            return
        else:
            self.weather_manager.set_weather(self.weather_list[self.current_loop])

        if self.current_trial:
            self.current_trial = Trial(self._vehicle, self._trial_settings, self.client, self.weather_list[self.current_loop], self.current_trial.trial_data_save_folder, self.current_trial.user_name)  # Copy over the data from the previous trial
        else:   # First trial
            self.current_trial = Trial(self._vehicle, self._trial_settings, self.client, self.weather_list[self.current_loop])

        self.current_trial.start()


    def tick(self, display, events):
        if self.trial_started:
            # Handle O/P trial navigation keys
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if self.current_trial.trial_data_save_folder != None:  # The username has to be populated before shifting
                        # Go back one trial (O key)
                        if event.key == pygame.K_o:
                            if self.current_loop > 0:
                                print("Going back one trial...")
                                self.current_loop -= 2  # because next_trial() increments it first
                                self.next_trial()
                            else:
                                print("Already at first trial — cannot go back.")
                        
                        # Skip ahead one trial (P key)
                        elif event.key == pygame.K_p:
                            if self.current_loop < self.TRIAL_NUM - 1:
                                print("Skipping ahead one trial...")
                                self.next_trial()
                            else:
                                print("Already at last trial — cannot skip ahead.")

            # Regular tick behavior (run the current trial)
            if self.current_trial:
                self.current_trial.run_state_machine(display, events)

                # Move to next trial if the current one is done
                if self.current_trial.current_state == Trial.STATE.UNKNOWN:
                    self.next_trial()



import pygame
def is_enter_button_pressed(self, event : pygame.event):
    if event.type == pygame.JOYBUTTONDOWN and event.button == self.next_trial_joystick_button:
        return True
    if event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
        return True
    return False
            

            