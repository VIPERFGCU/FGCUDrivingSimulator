import os
import numpy as np
import pandas as pd
from tqdm import tqdm

# Define paths for all modalities
DATA_PATHS = {
    "camera": "C:/carla_env/fgcu-carla/scripts/preprocessed/camera_npy",
    "lidar": "C:/carla_env/fgcu-carla/scripts/preprocessed/lidar",
    "radar": "C:/carla_env/fgcu-carla/scripts/preprocessed/radar",
    "vehicle_state": "C:/carla_env/fgcu-carla/scripts/preprocessed/vehicle_state",
}

OUTPUT_PATH = "C:/carla_env/fgcu-carla/scripts/preprocessed/combined"

def normalize_data(data):
    """Normalize data to range [0,1]. Handle empty or constant data."""
    data = np.array(data, dtype=np.float32)  # Ensure numerical format
    if np.max(data) > np.min(data): 
        return (data - np.min(data)) / (np.max(data) - np.min(data))
    return data

def load_npy(file_path):
    """Load and normalize .npy files."""
    return normalize_data(np.load(file_path).flatten())

def load_csv(file_path):
    """Load and normalize CSV files, ensuring numeric values only."""
    df = pd.read_csv(file_path)

    # Convert all columns to numeric (handle possible non-numeric data)
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

    return normalize_data(df.values.flatten())

def combine_modalities():
    """Combine all modalities into a single dataset."""
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    combined_data = []
    matched_files = 0

    for level in range(6):  # Levels 0–5
        print(f"\n🔍 Processing Level {level}...")

        # Define level-specific paths
        level_paths = {mod: os.path.join(path, f"level_{level}") for mod, path in DATA_PATHS.items()}

        # Ensure all directories exist
        for mod, path in level_paths.items():
            if not os.path.exists(path):
                print(f"🚨 Missing directory: {path}. Skipping Level {level}.")
                continue

        # Get list of filenames (only base names)
        filenames = set(f"level_{level}_{i+1:04d}" for i in range(1000))  # Expecting 1000 per level

        # Check if all modalities exist for each file
        for base_name in tqdm(filenames, desc=f"🔄 Merging Level {level}", unit="file"):
            try:
                # Construct full file paths
                camera_file = os.path.join(level_paths["camera"], f"{base_name}.npy")
                lidar_file = os.path.join(level_paths["lidar"], f"{base_name}.npy")
                radar_file = os.path.join(level_paths["radar"], f"{base_name}.csv")
                vehicle_state_file = os.path.join(level_paths["vehicle_state"], f"{base_name}.csv")

                # Check existence
                if not (os.path.exists(camera_file) and os.path.exists(lidar_file) and 
                        os.path.exists(radar_file) and os.path.exists(vehicle_state_file)):
                    print(f"⚠️ Skipping {base_name}: Missing modality data.")
                    continue

                # Load data
                camera_data = load_npy(camera_file)
                lidar_data = load_npy(lidar_file)
                radar_data = load_csv(radar_file)
                vehicle_state_data = load_csv(vehicle_state_file)

                # Concatenate all modalities into a single vector
                combined_vector = np.concatenate([camera_data, lidar_data, radar_data, vehicle_state_data])
                combined_data.append(combined_vector)
                matched_files += 1

            except Exception as e:
                print(f"❌ Error processing {base_name}: {e}")

    # Convert list to NumPy array and save
    if combined_data:
        combined_data = np.array(combined_data)
        output_file = os.path.join(OUTPUT_PATH, "combined_data.npy")
        np.save(output_file, combined_data)
        print(f"\n✅ Saved combined data with {matched_files} samples to {output_file}")
    else:
        print("\n❌ No matched data found. Check preprocessing and filenames.")

if __name__ == "__main__":
    combine_modalities()
