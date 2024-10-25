# FGCU Driving Simulator Project

This project implements a custom research trial system for the CARLA simulator, allowing researchers to conduct and record driving trials with various vehicles in a simulated environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Starting Trials](#starting-trials)
6. [Features](#features)
7. [File Structure](#file-structure)
8. [Data Logging](#data-logging)
9. [Customization](#customization)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)
12. [License](#license)

## Prerequisites

- CARLA Simulator (0.9.15)
- Python 3.7 (64-bit)
- Git (for cloning the repository)
- pip (should be included with Python 3.7)

## Installation

Follow these steps carefully to set up the FGCU Driving Simulator project:

1. Clone the VIPER Lab repository:
   ```
   git clone https://github.com/VIPERFGCU/FGCUDrivingSimulator.git
   ```

2. Navigate to the repository location:
   ```
   cd path\to\FGCUDrivingSimulator
   ```

3. Download CARLA:
   - Go to https://github.com/carla-simulator/carla/releases/tag/0.9.15
   - Download `CARLA_0.9.15.zip`
   - Extract the "WindowsNoEditor" folder to a location of your choice

4. Install Python 3.7 (64-bit):
   - If not already installed, download from https://www.python.org/downloads/release/python-370/
   - Choose the Windows x86-64 executable installer

5. Create a virtual environment for CARLA:
   ```
   path\to\Python37\python.exe -m venv carla_env
   ```
   Note: Replace `path\to\Python37` with your actual Python 3.7 installation path

6. Activate the CARLA Python environment:
   ```
   carla_env\Scripts\activate
   ```

7. Verify the Python version:
   ```
   python --version
   ```
   Ensure that it displays Python 3.7.0

8. Install required packages:
   ```
   pip install -r "path\to\FGCUDrivingSimulator\requirements.txt"
   ```
   Alternatively, install packages individually:
   ```
   pip install carla configparser DateTime numpy pygame pytz zope.interface
   ```

9. Navigate to the script folder:
   ```
   cd "path\to\FGCUDrivingSimulator\carla_project\ReseachCode"
   ```

10. Start the CARLA simulator:
    ```
    path\to\WindowsNoEditor\CarlaUE4.exe
    ```

11. Run the Python script:
    ```
    python manual_control_steeringwheel_Research_Base.py
    ```

### Note on File Paths

Replace `path\to\` in the above instructions with the actual paths on your system:
- `path\to\FGCUDrivingSimulator` might be `E:\FGCUDrivingSimulator`
- `path\to\Python37` might be `C:\Users\YourUsername\AppData\Local\Programs\Python\Python37`
- `path\to\WindowsNoEditor` might be `E:\WindowsNoEditor`

Adjust all paths according to your specific setup while maintaining the overall directory structure.

## Configuration

The project uses a configuration file `user_config.ini` to set various parameters:

- Axis mappings for steering wheel controls
- Key mappings for keyboard controls
- Trial settings (starting position, rotation, speed limit)
- Vehicle preferences
- Display units

Example configuration:

```ini
[AxisMapping]
steering = 0
throttle = 1
brake = 2
joy_reverse = 4
joy_handbrake = 4
steering_damping = 0.4
throttle_damping = 1.0
brake_damping = 1.0

[KeyMapping]
key_reverse = q
key_handbrake = k
key_toggle_headlights = l

[TrialSettings]
location_x = 246.3
location_y = -27.0
location_z = 1.0
rotation_pitch = 0.0
rotation_yaw = -86.76
rotation_roll = 0.0
speed_limit = 45.0

[Settings]
random_vehicle = False
default_vehicle = vehicle.dodge.charger_2020
speed_unit = mph
height_unit = ft
```

## Usage

1. Start the CARLA simulator by running CarlaUE4.exe as described in the installation steps.

2. Activate your Python 3.7 virtual environment if it's not already active.

3. Run the main script:
   ```
   python manual_control_steeringwheel_Research_Base.py
   ```

4. Optional command-line arguments:
   - `--host`: IP of the host server (default: 127.0.0.1)
   - `--port`: TCP port to listen to (default: 2000)
   - `--res`: Window resolution (default: 1280x720)
   - `--filter`: Actor filter (default: "vehicle.*")
   - `--town`: Specify which town to load (default: "Town03")

   Example:
   ```
   python manual_control_steeringwheel_Research_Base.py --res 1920x1080 --town Town05
   ```

## Starting Trials

1. Launch the script as described in the Usage section.
2. Press `Keypad 1` to initialize the trial setup.
3. Enter a user name or select from the dropdown.
4. Press `Enter` to start the trial.
5. Control the vehicle using keyboard or steering wheel.
6. Press `Spacebar` to end the trial.
7. View results and press `Enter` to start a new trial.

## Features

- Custom trial system with start and end functionality
- Speed tracking and violation recording
- User management system
- Data logging (CSV format) for each trial and session
- Configurable controls for both keyboard and steering wheel
- HUD with real-time information display
- Customizable vehicle selection
- Weather and town selection

## File Structure

- `manual_control_steeringwheel_Research_Base.py`: Main script
- `user_config.ini`: Configuration file for user settings
- `scripts/data/`: Directory for storing logged data
  - `runs_data_YYYY-MM-DD.csv`: Daily log of all trial runs
  - `totals_data_YYYY-MM-DD.csv`: Daily summary of trial totals
  - `Trial_events_YYYY-MM-DD.csv`: Log of specific events during trials
  - `memory/user_names.json`: Stored user names

## Data Logging

The script logs data in three main CSV files:

1. `runs_data_YYYY-MM-DD.csv`: Detailed data for each trial run
2. `totals_data_YYYY-MM-DD.csv`: Summary data for each completed trial
3. `Trial_events_YYYY-MM-DD.csv`: Specific events (e.g., speed violations) during trials

Data logged includes:

- User name
- Session and trial codes
- Timestamps
- Vehicle speed and position
- Violation events
- Trial duration and statistics

## Customization

- Modify `user_config.ini` to change control mappings, trial settings, and display preferences
- Edit the `TrialManager` class in the main script to adjust trial logic and data collection
- Customize the HUD display by modifying the `HUD` class
- Adjust vehicle dynamics by tweaking parameters in the `DualControl` class

## Troubleshooting

- Ensure you're using Python 3.7:
  ```
  python --version
  ```

- Verify you're using a 64-bit version:
  ```
  python -c "import struct; print(struct.calcsize('P') * 8)"
  ```
  This should output 64.

- If the wheel file installation fails, try:
  ```
  easy_install "path\to\WindowsNoEditor\PythonAPI\carla\dist\carla-0.9.15-cp37-cp37m-win_amd64.whl"
  ```

- As a last resort, add the CARLA Python API to your path manually:
  ```python
  import sys
  import os

  carla_path = r"path\to\WindowsNoEditor\PythonAPI\carla"
  sys.path.append(carla_path)
  ```

- Ensure the CARLA `WindowsNoEditor` folder is in your system's PATH environment variable.
- Verify steering wheel axis mappings in `user_config.ini` if controls are unresponsive
- Use `--help` command-line argument for additional script options
- If experiencing performance issues, try reducing the game resolution or graphics settings
- If you encounter module import errors, ensure your virtual environment is activated and all required packages are installed
- For CARLA-specific issues, refer to the official CARLA documentation
- Make sure the CARLA simulator (CarlaUE4.exe) is running before executing the Python script

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

Please ensure your code adheres to the project's coding standards and include appropriate tests if applicable.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

For additional information or support, please open an issue on the GitHub repository or contact the VIPER Lab team.
