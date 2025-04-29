# CARLA Simulation Trial Management

_Last Updated: December 2025 — Johnny Mai_

---

## Overview
This script manages a CARLA simulation trial, tracks user driving behavior, and logs data into CSV files.  
The system monitors speed violations, zone performance, and overall driving statistics while allowing multiple trials per user.  
This project is designed for future students to continue research, analysis, or modifications.

---

## Features
- **Speed Violation Tracking**: Logs when and where speed limits are exceeded.
- **Zone Performance Analysis**: Tracks time spent in specific map zones and violations.
- **Interval Data Logging**: Saves speed, position, and timestamps at regular intervals.
- **Trial System**: Supports up to 7 trials per user with structured data collection.
- **Weather Conditions Tracking**: Saves weather presets to compare driving performance.
- **User Management**: Stores trial data per user in a dedicated folder.
- **Autopilot & Manual Mode Support**: Allows autonomous driving testing.
- **Logitech Wheel Support**: Users drive using a Logitech racing wheel for steering, acceleration, and braking.
- **[Future] Traffic Vehicle Support**: Future updates will allow spawning AI-controlled background vehicles.

---

## File Structure
```
project_root/
│── data/
│   ├── csv/  # Stores all trial CSV data
│   │   ├── <user_name>/  # Each user has a dedicated folder
│   │   │   ├── violation_data_<trial>_<date>.csv
│   │   │   ├── zones_data_<trial>_<date>.csv
│   │   │   ├── interval_data_<trial>_<date>_<weather>.csv
│   │   │   ├── overall_data_<trial>_<date>.csv
│── fgcu-carla/
│   ├── scripts/
│   │   ├── python/
│   │   │   ├── fgcu_carla_trial.py  # Main script for conducting trials
│── config_handler.py  # Configuration manager for user settings
│── trial_manager.py  # Handles trial execution & logging
│── world_manager.py  # Manages CARLA world, vehicles, and sensors
│── README.md  # Documentation
```

---

## CSV File Details

| CSV Name | Description |
|:---|:---|
| **violation_data_<trial>_<date>.csv** | Records every instance of speeding (timestamp, speed, location). |
| **zones_data_<trial>_<date>.csv** | Tracks when drivers enter/exit predefined map zones and violations that occur inside zones. |
| **interval_data_<trial>_<date>_<weather>.csv** | Records driver’s speed, position (X, Y, Z), and timestamp at regular intervals (e.g., every 1–2 seconds) with weather conditions. |
| **overall_data_<trial>_<date>.csv** | Summarized statistics for the full trial: average speed, trial duration, total violations, and weather setting. |

---

## [Future] Adding Traffic Vehicles (Planned Feature)

**Note:** Traffic vehicle spawning is not implemented yet.  
Future students can add traffic using the CARLA API:

**Recommended Traffic Addition Steps:**
1. Modify `world_manager.py` to add a `spawn_traffic()` function.
2. Use the CARLA blueprint library (`vehicle.*`) to spawn vehicles at spawn points.
3. Enable autopilot on those vehicles.
4. Optionally, log traffic collisions or behaviors into new CSV files.

**Impact:**  
Adding traffic will allow testing driver behavior under dynamic and realistic conditions.

---

## Installing CARLA on School Computers (By Johnny Mai)

1. Download **Python 3.7.0**
2. Download **CARLA** from the official website (recommend placing it in `C:\` for easy access).
3. Download and install **CMake**.
4. Find Python Path:  
   - Open File Explorer, locate Python 3.7.0
   - Or run `where python` in Command Prompt.
5. Set up a Virtual Environment:
   ```
   python -m venv carla_env
   carla_env\Scripts\activate
   ```
6. Install CARLA Python API:
   ```
   cd path\to\CARLA\PythonAPI\carla
   python --version
   python -m pip install --upgrade pip
   pip install .
   ```
   - If failure: manually install the `.egg` file from `CARLA/PythonAPI/Carla/dist`.
   - Also install dependencies:
   ```
   pip install pygame numpy
   ```
7. Start the CARLA Simulator:
   ```
   cd carla_env\carla
   carlaue4.exe
   ```
8. Test using Example Script:
   ```
   cd ../examples
   python manual_control.py
   ```

---

## Running FGCU CARLA Trial

1. Activate the Virtual Environment:
   ```
   carla_env\Scripts\activate
   ```
2. Start the CARLA Simulator:
   ```
   cd carla_env\carla
   carlaue4.exe
   ```
3. Navigate to the Script Directory:
   ```
   cd carla_env\fgcu-carla\scripts
   ```
4. Start the Trial Script:
   ```
   python fgcu_carla_trial.py
   ```
5. **Pre-Trial Free Drive**:
   - Drive around freely to get used to the simulator.
   - Use Logitech wheel for steering, throttle, braking.
   - Once comfortable, **press [1]** to start a trial.

6. **Starting a Trial**:
   - After pressing [1], **enter your exact username** in Command Prompt.
   - This will create/save into your user folder for all 7 trials.
   - Then return to Pygame window and drive normally.

7. **Ending a Trial**:
   - Press **[SPACEBAR]** to end a trial.
   - Press **[ESC]** to exit or start a new trial.

8. **Repeat**:
   - Complete 7 trials per user.

9. **Survey Completion**:
   - Once trials are completed, fill out the provided post-trial survey.

---

## Future Improvements

- Replace Command Prompt username input with full **Pygame UI**.
- Add **AI Traffic Vehicles** to simulate real-world driving.
- **Database Integration** for better data analysis.
- **Machine Learning** models to predict driving behaviors.
- **Visualization Tools** (heatmaps, violation trend graphs).
- Explore **VR headset compatibility** (Oculus, Vive).

---

# FGCU CARLA Driving Trial Codebase - Full Technical Documentation

## System Architecture

```
CARLA Server (simulator) 
        ↓
 Python Client (your scripts)
        ↓
 World Manager — handles vehicle, world, weather
        ↓
 Trial Manager — handles user trials and CSV data saving
        ↓
 HUD/Controller — visual interface + steering inputs
        ↓
 Data Output — 4 CSV files per trial
```

---

## Class-by-Class Detailed Explanation

### Zone
- Defines rectangular map areas.
- Tracks entry/exit times, average speeds, speeding violations.

### TrialManager
- Manages sessions, trials, CSV saving.
- Tracks user speed, trial duration, violations.

### World
- Loads the CARLA world.
- Manages vehicle spawns, weather, and sensors.

### HUD
- Displays speedometer, map, headings, collision warnings.

### CameraManager
- Manages cameras: RGB, Depth, Segmentation, LiDAR.

### CollisionSensor, LaneInvasionSensor, GnssSensor
- CollisionSensor: Detects vehicle collisions.
- LaneInvasionSensor: Detects lane crossing.
- GnssSensor: Tracks GPS coordinates.

### ConfigHandler
- Loads joystick mappings and other settings from `user_config.ini`.

### DualControl
- Manages Logitech wheel and keyboard inputs.

### HelpText, FadingText
- Help menu, notifications on screen.

---

## Key Functions and Utilities

| Function | Description |
|:---|:---|
| `find_weather_presets()` | Lists all available weather modes. |
| `update_player_position()` | Checks and updates the player's current zone. |
| `display_current_zone()` | Displays the zone label on screen. |
| `check_user_position()` | Detects zone entry/exit. |
| `get_actor_display_name()` | Formats readable vehicle names. |

---

## Game Loop Process

1. Launch simulation → Load vehicle → Free drive mode
2. Press [1] → Enter username
3. Drive under trial conditions
4. End trial by [SPACEBAR]
5. View trial results
6. Repeat up to 7 trials
7. Submit post-trial survey

---

## Future Expansion Points

- Add **background traffic** using `spawn_actor()`.
- Store CSV data into **relational databases**.
- Add **VR support**.
- **Live plot visualization** during driving.
- **Deep Learning models** for prediction based on driving behavior.

---

# Contact

For any questions, setup issues, or maintenance needs,  
please contact **Johnny Mai** or refer to this documentation.

---

