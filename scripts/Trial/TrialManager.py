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
            "CloudyNight"
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
            # Check if a trial exist
            self.current_trial.run_state_machine(display, events)    # This also renders and Records

            # The trial is over. Call the next trial
            if self.current_trial.current_state == Trial.STATE.UNKNOWN:
                if self.current_trial == self.TRIAL_NUM - 1:    # Trial starts from 0
                    self.trial_started = False
                else:
                    self.next_trial()
            

            