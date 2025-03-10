import os

# Base paths
input_base_path = "C:/carla_env/fgcu-carla/scripts/output"
preprocessed_base_path = "C:/carla_env/fgcu-carla/scripts/preprocessed"

# Folder categories to process
categories = ['camera', 'lidar', 'radar', 'vehicle_state']

# Levels to process
levels = [f"level_{i}" for i in range(6)]  # levels 0 to 5

# Create preprocessed folders
for category in categories:
    category_input_path = os.path.join(input_base_path, category)
    category_preprocessed_path = os.path.join(preprocessed_base_path, category)
    
    # Create category folder in preprocessed path
    os.makedirs(category_preprocessed_path, exist_ok=True)
    
    for level in levels:
        level_preprocessed_path = os.path.join(category_preprocessed_path, level)
        os.makedirs(level_preprocessed_path, exist_ok=True)
        print(f"Created: {level_preprocessed_path}")

print("Preprocessed folders created successfully.")
