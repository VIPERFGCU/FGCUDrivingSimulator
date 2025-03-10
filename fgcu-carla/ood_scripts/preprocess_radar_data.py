import os
import pandas as pd
import random
import shutil

def preprocess_radar_data(input_folder, output_folder):
    """Preprocess radar data into CSV format and provide file totals."""
    total_processed = 0
    level_counts = {}

    for level in range(6):  # Levels 0–5
        level_input = os.path.join(input_folder, f"level_{level}")
        level_output = os.path.join(output_folder, f"level_{level}")
        os.makedirs(level_output, exist_ok=True)

        if not os.path.exists(level_input):
            print(f"Directory {level_input} does not exist. Skipping level {level}.")
            level_counts[level] = 0
            continue

        count = 0
        for file in os.listdir(level_input):
            if file.endswith(".txt"):
                file_path = os.path.join(level_input, file)
                output_file = os.path.join(level_output, f"level_{level}_{count + 1}.csv")  # Renamed file

                try:
                    # Read radar data
                    radar_data = []
                    with open(file_path, 'r') as f:
                        for line in f:
                            depth, azimuth, altitude, velocity = map(float, line.strip().split(','))
                            radar_data.append([depth, azimuth, altitude, velocity])

                    # Save as `.csv`
                    df = pd.DataFrame(radar_data, columns=["Depth", "Azimuth", "Altitude", "Velocity"])
                    df.to_csv(output_file, index=False)
                    print(f"Processed and saved: {output_file}")

                    count += 1
                    total_processed += 1

                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")

        level_counts[level] = count
        print(f"Processed {count} files for level_{level}")

    print("\nPreprocessing Summary:")
    for level, count in level_counts.items():
        print(f"Level {level}: {count} files")
    print(f"Total processed files: {total_processed}")

    return level_counts


def balance_radar_data(output_folder, level_counts, balance_to='min'):
    """Balance radar data by undersampling or oversampling."""
    if balance_to == 'min':
        target_count = min(level_counts.values())  # Balance to smallest class
    elif balance_to == 'max':
        target_count = max(level_counts.values())  # Balance to largest class
    else:
        raise ValueError("balance_to must be either 'min' or 'max'.")

    for level in range(6):
        level_output = os.path.join(output_folder, f"level_{level}")
        files = os.listdir(level_output)

        if len(files) > target_count:
            # Undersample
            files_to_keep = random.sample(files, target_count)
            for file in files:
                if file not in files_to_keep:
                    os.remove(os.path.join(level_output, file))
                    print(f"Removed (undersampled): {file}")
        elif len(files) < target_count:
            # Oversample
            while len(files) < target_count:
                file_to_duplicate = random.choice(files)
                file_name, file_ext = os.path.splitext(file_to_duplicate)
                new_file = f"{file_name}_copy{len(files) + 1}{file_ext}"
                shutil.copy(
                    os.path.join(level_output, file_to_duplicate),
                    os.path.join(level_output, new_file)
                )
                files.append(new_file)
                print(f"Duplicated (oversampled): {file_to_duplicate}")

        print(f"Balanced level_{level} to {target_count} files.")

    print("\nBalancing Summary:")
    for level in range(6):
        level_output = os.path.join(output_folder, f"level_{level}")
        print(f"Level {level}: {len(os.listdir(level_output))} files")


if __name__ == "__main__":
    # Step 1: Preprocess Radar Data
    output_folder = "C:/carla_env/fgcu-carla/scripts/preprocessed/radar"
    level_counts = preprocess_radar_data(
        "C:/carla_env/fgcu-carla/scripts/output/radar",  # Input folder
        output_folder  # Output folder
    )

    # Step 2: Balance the Dataset (if needed)
    if max(level_counts.values()) != min(level_counts.values()):
        print("\nDataset is imbalanced. Balancing now...")
        balance_radar_data(output_folder, level_counts, balance_to='min')  # Adjust 'min' or 'max'
    else:
        print("\nDataset is already balanced. No balancing needed.")
