import os
import pandas as pd
import random
from tqdm import tqdm

def preprocess_vehicle_state(input_folder, output_folder, target_samples=1000):
    """
    Preprocess vehicle state data from text to CSV format.
    Ensures each level folder contains exactly target_samples files.
    """
    total_processed = 0
    level_counts = {}

    # Create error log file
    error_log_file = os.path.join(output_folder, "error_log.txt")
    if os.path.exists(error_log_file):
        os.remove(error_log_file)

    # Process each weather level (0–5)
    for level in range(6):
        level_input = os.path.join(input_folder, f"level_{level}")
        level_output = os.path.join(output_folder, f"level_{level}")
        os.makedirs(level_output, exist_ok=True)

        if not os.path.exists(level_input):
            print(f"Directory {level_input} does not exist. Skipping level {level}.")
            level_counts[level] = 0
            continue

        files = [file for file in os.listdir(level_input) if file.endswith(".txt")]

        # Shuffle and sample files if exceeding target_samples
        if len(files) > target_samples:
            files = random.sample(files, target_samples)
        elif len(files) < target_samples:
            print(f"Warning: Level {level} has fewer files ({len(files)}) than target_samples ({target_samples}).")
        
        count = 0
        for file in tqdm(files, desc=f"Processing level_{level}"):
            file_path = os.path.join(level_input, file)
            output_file = os.path.join(level_output, f"level_{level}_{count + 1:04d}.csv")  # Renamed systematically

            try:
                # Parse the vehicle state data
                with open(file_path, 'r') as f:
                    data = f.read().strip()

                # Extract position, rotation, and velocity
                position = data.split("Position: ")[1].split(", Rotation: ")[0].strip()
                rotation = data.split("Rotation: ")[1].split(", Velocity: ")[0].strip()
                velocity = data.split("Velocity: ")[1].strip()

                # Format the data into a DataFrame
                df = pd.DataFrame([[position, rotation, velocity]], columns=["Position", "Rotation", "Velocity"])
                df.to_csv(output_file, index=False)

                count += 1
                total_processed += 1

            except Exception as e:
                # Log errors to the error log
                with open(error_log_file, 'a') as error_log:
                    error_log.write(f"Error processing {file_path}: {e}\n")
                print(f"Error processing file {file_path}: {e}. Skipping this file.")

        # Record the count for the current level
        level_counts[level] = count
        print(f"Processed {count} files for level_{level}")

    # Summary of preprocessing
    print("\nPreprocessing Summary:")
    for level, count in level_counts.items():
        print(f"Level {level}: {count} files")
    print(f"Total processed files: {total_processed}")

    return level_counts


if __name__ == "__main__":
    preprocess_vehicle_state(
        "C:/carla_env/fgcu-carla/scripts/output/vehicle_state",  # Input folder
        "C:/carla_env/fgcu-carla/scripts/preprocessed/vehicle_state",  # Output folder
        target_samples=1000  # Ensure each level has 1000 samples
    )
