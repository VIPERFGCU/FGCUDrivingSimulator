import os
import pygame   # For key presses
import carla
import time     # For countdown timer in Ready State.
from enum import Enum   # For states
import datetime

from Sensors.ViolationLogger import ViolationLogger
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
        UNKNOWN = 4 # When no trial is being run at all

    def __init__(self, vehicle: Vehicle, trial_settings, client: carla.Client, trial_weather : str, trial_data_save_folder = None, user_name = ""):
        # For copying to other trial objects
        self.trial_data_save_folder = trial_data_save_folder
        self.user_name = user_name

        self.vehicle = vehicle  # The Vehicle to track through the trials
        self.client = client
        self.world = client.get_world()
        self.trial_weather = trial_weather

        self.current_state = self.STATE.UNKNOWN   # Is only changed in _switch_state

        # SETUP state global flag
        self.user_name_entered = False
        if self.user_name != "":
            self.user_name_entered = True

        # SETUP state end

        self.trial_data_file_name = self.trial_weather + ".rec"

        if self.user_name_entered:  # This is called again in setup after the player inputs their username if it wasn't already set
            self.trial_recorder = ScenarioRecorder(vehicle.get_player(), client, trial_data_save_folder, self.trial_data_file_name)
            self.violation_logger = ViolationLogger(self.trial_recorder, vehicle.get_player(), client.get_world())         # Records sensor violations( Such as the lane invasion sensor ). It does not record the speed violation. That is handled by _RUNNING function
        self.trial_settings = trial_settings

        # The left side of the wall to the right side of the wall before the tunnel. WARNING. UE COORDS
        self.end_line = [(22480.000000/100.0, -1470.869751/100.0), (25246.058594/100.0, -1470.869751/100.0)]

        # UI variables. Setup TrialHUD
        self.start_screen_enabled = False
        self.count_down_screen_enabled = True

        # READY state global class variables
        self.count_down_start_time = 0
            

        # RUNNING State global Variables
        self.next_trial_joystick_button = vehicle.vehicle_controller.input_mapping.get_axis('next_trial')
        self.start_time = 0.0
        self.end_time = 0.0
        self.start_passed = False
        self.line_crossed_last_frame = False
        self.violated_last_frame = False    # For speed violation. Only count when person goes over speed limit.
        

    def start(self):
        self._switch_state(self.STATE.SETUP)

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
            self._COMPLETED(display, events)

        else:
            # print("Unknown state.")
            pass
        
        

    # IMPORTANT: THIS SHOULD ONLY BE CALLED BY THE STATE FUNCTIONS
    def _switch_state(self, new_state):
        # Reset all state dependent variables
        self.results_screen_enabled = False
        self.start_screen_enabled = False
        self.count_down_screen_enabled = False

        # Reset all state dependent variables
        self.count_down_start_time = 0
        self.count_down_enabled = False

        self.start_passed = False
        self.line_crossed_last_frame = False


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
            self.start_passed = False

            print("State changed to RUNNING.")

        elif new_state == self.STATE.COMPLETED:
            # Handle COMPLETED state
            self.end_trial()    # Store the results

            # Show the visual results. Will be ~0.3 seconds at most off from the actual due to pythons GIL
            self.trial_time = self.world.get_snapshot().timestamp.elapsed_seconds - self.start_time
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
                if self.is_enter_button_pressed(event):
                    self.user_name_entered = True   # End the user input
                
            UI.render_user_prompt_screen(display, self.user_name)
        else:
            if self.trial_data_save_folder == None:
                self.trial_data_save_folder = os.path.join(self.trial_settings["data_save_location"], self.user_name + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
            
            self.trial_recorder = ScenarioRecorder(self.vehicle.get_player(), self.client, self.trial_data_save_folder, self.trial_data_file_name)
            self.violation_logger = ViolationLogger(self.trial_recorder, self.vehicle.get_player(), self.client.get_world())
            
            self._switch_state(self.STATE.READY)
        

    def _READY(self, display, events):
        count_down_time = 5 # 5 second count down

        # Reset velocities contously
        self.vehicle.get_player().set_target_velocity(carla.Vector3D(0, 0, 0))
        self.vehicle.get_player().set_target_angular_velocity(carla.Vector3D(0, 0, 0))

        # Start countdown after enter is pressed
        if self.start_screen_enabled:
            for event in events:
                if self.is_enter_button_pressed(event):
                    self.start_screen_enabled = False
                    self.count_down_start_time = time.time()

        if self.start_screen_enabled:
            UI.render_start_screen(display)
        elif time.time() - self.count_down_start_time < count_down_time:  # 5 second count down
            UI.render_count_down_screen(display, count_down_time - int(time.time() - self.count_down_start_time))
        else:
            self._switch_state(self.STATE.RUNNING)

    
    def _RUNNING(self, display):
        if self._check_if_end_line_is_crossed():   # Check to see if the finish line is crossed( I'm tired and need to rewrite this comment)
            if( not self.line_crossed_last_frame and self.start_passed == True ):
                self._switch_state(self.STATE.COMPLETED)
            elif(not self.start_passed):
                self.start_passed = True
                self.trial_recorder.start()     # Start the recorder when they touch the starting line
                self.start_time = self.world.get_snapshot().timestamp.elapsed_seconds   # Take the time the moment the start line was passed
                print("Start Passed")
            
            self.line_crossed_last_frame = True
        else:
            self.line_crossed_last_frame = False

        speed = self.vehicle.get_speed()
        UI.render_speed(display, speed)
        if speed > self.trial_settings["max_speed_limit"]:
            if not self.violated_last_frame:
                self.trial_recorder.log_event("violation_speed")    # Violation logged

            UI.render_speed_warning(display)
            self.violated_last_frame = True
        else:
            self.violated_last_frame = False
            
    
    
    def _COMPLETED(self, display, events):
        if self.results_screen_enabled:
            UI.render_results(display, self.trial_time)
            for event in events:
                if self.is_enter_button_pressed(event):
                    self.results_screen_enabled = False
        else:
            self._switch_state(self.STATE.UNKNOWN)

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
        self.vehicle.get_player().set_transform(transform)

        # Reset velocities
        self.vehicle.get_player().set_target_velocity(carla.Vector3D(0, 0, 0))
        self.vehicle.get_player().set_target_angular_velocity(carla.Vector3D(0, 0, 0))

        # Attach Sensors
        self.violation_logger.attach_lane_invasion_sensor()
    
    
    def end_trial(self):
        self.trial_recorder.stop()
        self.violation_logger.destroy()

    # THIS WAS MADE BY CHATGPT. NOT VETTED. It works?
    def _check_if_end_line_is_crossed(self):
        player_obj = self.vehicle.get_player()
        # --- Get vehicle bounding box corners in world coords ---
        transform = player_obj.get_transform()
        bb = player_obj.bounding_box
        extent = bb.extent

        # 4 corners of the box (local coordinates)
        corners_local = [
            carla.Location(x= extent.x, y= extent.y, z=0.0),
            carla.Location(x= extent.x, y=-extent.y, z=0.0),
            carla.Location(x=-extent.x, y=-extent.y, z=0.0),
            carla.Location(x=-extent.x, y= extent.y, z=0.0)
        ]

        # transform to world
        corners_world = [transform.transform(c) for c in corners_local]

        # close polygon
        bb_edges = list(zip(corners_world, corners_world[1:] + corners_world[:1]))

        # --- End line segment ---
        line_start = carla.Location(x=self.end_line[0][0], y=self.end_line[0][1], z=0.0)
        line_end   = carla.Location(x=self.end_line[1][0], y=self.end_line[1][1], z=0.0)

        # --- Helper: check if two line segments intersect ---
        def segments_intersect(p1, p2, q1, q2):
            def ccw(a, b, c):
                return (c.y - a.y) * (b.x - a.x) > (b.y - a.y) * (c.x - a.x)
            return (ccw(p1, q1, q2) != ccw(p2, q1, q2)) and \
                (ccw(p1, p2, q1) != ccw(p1, p2, q2))

        # --- Check intersection between end line and each bbox edge ---
        for edge_start, edge_end in bb_edges:
            if segments_intersect(edge_start, edge_end, line_start, line_end):
                return True

        return False

    # Helper function to handle both joystick and keyboard input
    def is_enter_button_pressed(self, event : pygame.event):
        if event.type == pygame.JOYBUTTONDOWN and event.button == self.next_trial_joystick_button:
            return True
        if event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
            return True
        return False

