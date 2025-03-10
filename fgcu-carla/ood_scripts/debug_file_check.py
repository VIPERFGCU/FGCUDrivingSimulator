import os

# Paths to preprocessed data
DATA_FOLDERS = {
    "camera": "C:/carla_env/fgcu-carla/scripts/preprocessed/camera_npy",
    "lidar": "C:/carla_env/fgcu-carla/scripts/preprocessed/lidar",
    "radar": "C:/carla_env/fgcu-carla/scripts/preprocessed/radar",
    "vehicle_state": "C:/carla_env/fgcu-carla/scripts/preprocessed/vehicle_state",
}

def count_files(folder, extension):
    """Count the number of files with a given extension in a folder."""
    if not os.path.exists(folder):
        return 0
    return len([f for f in os.listdir(folder) if f.endswith(extension)])

def check_data_integrity():
    """Check that all modalities have matching file counts for each level."""
    print("\n🔍 **Checking Data Integrity Across All Modalities**\n")
    file_counts = {}

    for level in range(6):  # Levels 0-5
        level_counts = {}

        for modality, folder in DATA_FOLDERS.items():
            level_folder = os.path.join(folder, f"level_{level}")
            extension = ".npy" if modality in ["camera", "lidar"] else ".csv"

            count = count_files(level_folder, extension)
            level_counts[modality] = count

        file_counts[level] = level_counts

    # Display file counts and check for mismatches
    total_matched = 0
    for level, counts in file_counts.items():
        print(f"📂 **Level {level}:**")
        for modality, count in counts.items():
            print(f"   ✅ {modality.capitalize()}: {count} files")

        # Check if all modalities have the same count
        unique_counts = set(counts.values())
        if len(unique_counts) > 1:
            print("   ❌ **File count mismatch!** Please check for missing data.\n")
        else:
            total_matched += counts["camera"]  # Use camera count as reference

    print(f"\n🔍 **Matched {total_matched} samples across all levels**\n")
    print("✅ **Debug Check Complete!** ✅")

if __name__ == "__main__":
    check_data_integrity()
