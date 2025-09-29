import pygame   # For key presses
import carla
import time     # For countdown timer in Ready State.
from enum import Enum   # For states

from Trial.TrialUIObjects import UI
from Vehicle.Vehicle import Vehicle
from Trial.DataCollector import ScenarioRecorder

class Trial:
    # Trial State Machine
    '''
        There are 5 states:
            SETUP: Name is entered here
                - Goes to READY after name is entered.
            READY: Trial start screen is displayed. Countdown to 0 starts after enter is pressed.
                - Goes to RUNNING after key "Enter" is pressed
            RUNNING: Driving is enabled and player drives the loop. Recorder is started here
                - Goes to COMPLETED after zone 1 is entered and zone 8 is exited.
            COMPLETED: Trial is finished.
                - This class should be destroyed.
    '''
    class STATE(Enum):
        SETUP = 0
        READY = 1
        RUNNING = 2
        COMPLETED = 3

    def __init__(self, vehicle: Vehicle, world, trial_settings, client, trial_data_save_folder, trial_data_file_name = None, user_name = ""):
        self.vehicle = vehicle  # The Vehicle to track through the trials

        self.current_state = None   # Is only changed in _switch_state

        self.trial_recorder = ScenarioRecorder(client, trial_data_save_folder, trial_data_file_name)

        self.trial_settings = trial_settings

        # UI variables. Setup TrialHUD
        self.start_screen_enabled = False
        self.count_down_screen_enabled = True

        # READY state global class variables
        self.count_down_start_time = 0

        # SETUP state global flag
        self.user_name = ""
        self.user_name_entered = False
        if user_name != "":
            self.user_name_entered = True
            self.user_name = user_name

        # RUNNING State global Variables
        self.start_time = 0.0
        self.end_time = 0.0


    # Run every tick when a trial is active
    def run_state_machine(self, display, events):
        if self.current_state == self.STATE.SETUP:
            # Handle SETUP state
            # print("System is setting up.")
            self._SETUP(display, events)

        elif self.current_state == self.STATE.READY:
            # Handle READY state
            # print("System is ready.")
            self._READY(display, events)

        elif self.current_state == self.STATE.RUNNING:
            # Handle RUNNING state
            # print("System is running.")
            self._RUNNING(display)
            
        elif self.current_state == self.STATE.COMPLETED:
            # Handle COMPLETED state
            # print("System has completed.")
            self._COMPLETED(display)

        else:
            print("Unknown state.")
        
        

    # IMPORTANT: THIS SHOULD ONLY BE CALLED BY THE STATE FUNCTIONS
    def _switch_state(self, new_state):
        # Reset all state dependent variables
        self.results_screen_enabled = False
        self.start_screen_enabled = False
        self.count_down_screen_enabled = False

        # Reset all state dependent variables
        self.count_down_start_time = 0
        self.count_down_enabled = False


        # Set the settings for the new state
        if new_state == self.STATE.SETUP:
            # Handle SETUP state
            print("State changed to SETUP")

        elif new_state == self.STATE.READY:
            # Handle READY state
            self.start_screen_enabled = True
            self.count_down_screen_enabled = False
            self.count_down_start_time = 0

            self.prepare_trial()
            print("State changed to READY")

        elif new_state == self.STATE.RUNNING:   # Start the trial
            # Handle RUNNING state
            self.start_trial()
            print("State changed to RUNNING.")

        elif new_state == self.STATE.COMPLETED:
            # Handle COMPLETED state
            self.end_trial()    # Calculate all of the results
            self.results_screen_enabled = True
            print("System has completed.")

        
        else:
            print("Unknown state.")
        
        # Update the state
        self.current_state = new_state
        

    def _SETUP(self, display, events):
        if not self.user_name_entered:
            # User name input
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.unicode.isalpha():  # Accept only alphabetic characters
                        self.user_name += event.unicode
                    elif event.key == pygame.K_BACKSPACE:   # Delete a character
                        self.user_name = self.user_name[:-1]
                    elif event.key == pygame.K_SPACE:   # Add space
                        self.user_name += " "
                    elif event.key == pygame.K_RETURN:
                        self.user_prompt_screen_enabled = False # End the user input
                
            UI.render_user_prompt_screen(display, self.user_name)
        else:
            self._switch_state(self.STATE.READY)
        

    def _READY(self, display, events):
        count_down_time = 5 # 5 second count down

        # Start countdown after enter is pressed
        if self.start_screen_enabled:
            for event in events:
                if event.key == pygame.K_RETURN:
                    self.start_screen_enabled = False

        if self.start_screen_enabled:
            UI.render_start_screen(display)
        elif time.time() - self.count_down_start_time < count_down_time:  # 5 second count down
            UI.render_count_down_screen(display, self.count_down_start_time - int(time.time()))
        else:
            self._switch_state(self.STATE.RUNNING)

    
    def _RUNNING(self, display):
        margin = 1.0
        end_box = [240.70, 130.50, 244.36, -11.00]  # Bounding box for end of trial( cross this to finish )
        pos = self.vehicle.get_position()
        
        if( (end_box[0] - margin <= pos.x <= end_box[2] + margin or end_box[2] - margin <= pos.x <= end_box[0] + margin) and
               (end_box[1] - margin <= pos.y <= end_box[3] + margin or end_box[3] - margin <= pos.y <= end_box[1] + margin) ):    # Check to see if the finish line is crossed( I'm tired and need to rewrite this comment)
            self._switch_state(self.STATE.COMPLETED)
        else:
            speed = self.vehicle.get_speed()
            UI.render_speed(display, speed)
            if speed > self.trial_settings["max_speed"]:
                UI.render_speed_warning(display)
            # if self.vehicle.lane_invasion_sensor.is_line_just_crossed(): <- No point for this right now
            
    
    
    def _COMPLETED(self, display):
        if self.results_screen_enabled:
            self.render_results(display)
        else:
            self._switch_state(self.STATE.READY)

    # Teleport the player to the start location and rotate
    def prepare_trial(self):
        teleport_location = carla.Location(
            x=self.trial_settings['location_x'], 
            y=self.trial_settings['location_y'], 
            z=self.trial_settings['location_z']
        )
        teleport_rotation = carla.Rotation(
            pitch=self.trial_settings['rotation_pitch'], 
            yaw=self.trial_settings['rotation_yaw'], 
            roll=self.trial_settings['rotation_roll']
        )
        transform = carla.Transform(teleport_location, teleport_rotation)
        self.vehicle.set_vehicle_transform(transform)

    
    def start_trial(self):
        # Only storing the start time atm
        self.start_time = time.time()

