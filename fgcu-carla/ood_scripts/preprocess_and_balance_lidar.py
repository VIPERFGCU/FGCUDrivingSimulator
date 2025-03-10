import os
import numpy as np
import random
import shutil

def preprocess_and_balance_lidar(input_folder, output_folder, target_count=6000):
    """Preprocess LiDAR data, balance the dataset, and display file totals."""
    total_processed = 0
    level_counts = {}

    for level in range(6):  # Levels 0–5
        level_input = os.path.join(input_folder, f"level_{level}")
        level_output = os.path.join(output_folder, f"level_{level}")
        os.makedirs(level_output, exist_ok=True)

        count = 0
        files = os.listdir(level_input)

        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(level_input, file)
                output_file = os.path.join(level_output, f"level_{level}_{count + 1}.npy")  # Renamed file

                # Check if the file already exists
                if os.path.exists(output_file):
                    print(f"File already exists, skipping: {output_file}")
                    continue

                try:
                    # Load raw LiDAR data
                    with open(file_path, 'r') as f:
                        points = eval(f.read())  # Convert text representation to a list

                    # Save as NumPy array
                    np.save(output_file, np.array(points))
                    print(f"Processed and saved: {output_file}")

                    count += 1
                    total_processed += 1

                except Exception as e:
                    # Handle invalid or corrupted files
                    print(f"Error processing file {file_path}: {e}. Deleting file.")
                    os.remove(file_path)

        # Store the processed count
        level_counts[level] = count

        # Balance the dataset (undersample or oversample)
        processed_files = os.listdir(level_output)
        if len(processed_files) > target_count:
            # Undersample
            files_to_keep = random.sample(processed_files, target_count)
            for file in processed_files:
                if file not in files_to_keep:
                    os.remove(os.path.join(level_output, file))
                    print(f"Removed (undersampled): {file}")
        elif len(processed_files) < target_count:
            # Oversample
            while len(processed_files) < target_count:
                file_to_duplicate = random.choice(processed_files)
                file_name, file_ext = os.path.splitext(file_to_duplicate)
                new_file = f"{file_name}_copy{len(processed_files) + 1}{file_ext}"
                shutil.copy(
                    os.path.join(level_output, file_to_duplicate),
                    os.path.join(level_output, new_file)
                )
                processed_files.append(new_file)
                print(f"Duplicated (oversampled): {file_to_duplicate}")

        # Update the count after balancing
        level_counts[level] = len(os.listdir(level_output))
        print(f"Balanced level_{level} to {target_count} files.")

    print("\nFinal Dataset Totals:")
    for level, count in level_counts.items():
        print(f"Level {level}: {count} files")
    print(f"Total processed and balanced files: {sum(level_counts.values())}")

if __name__ == "__main__":
    preprocess_and_balance_lidar(
        "C:/carla_env/fgcu-carla/scripts/output/lidar",  # Input folder
        "C:/carla_env/fgcu-carla/scripts/preprocessed/lidar",  # Output folder
        target_count=6000  # Desired number of files per level
    )
