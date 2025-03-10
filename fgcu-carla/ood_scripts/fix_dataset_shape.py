import numpy as np

# Path to the dataset
DATASET_PATH = "C:/carla_env/fgcu-carla/scripts/preprocessed/combined/combined_data.npy"
FIXED_DATASET_PATH = "C:/carla_env/fgcu-carla/scripts/preprocessed/combined/fixed_combined_data.npy"

# Load the dataset
print(f"📂 Loading dataset from: {DATASET_PATH}")
data = np.load(DATASET_PATH, allow_pickle=True)

# Determine the maximum length
max_length = max(len(sample) for sample in data)
print(f"🔍 Maximum sample length: {max_length}")

# Pad or truncate all samples to match the max length
fixed_data = np.array([np.pad(sample, (0, max_length - len(sample)), mode='constant') if len(sample) < max_length else sample[:max_length] for sample in data])

# Save the fixed dataset
np.save(FIXED_DATASET_PATH, fixed_data)
print(f"✅ Saved fixed dataset with shape {fixed_data.shape} to: {FIXED_DATASET_PATH}")
