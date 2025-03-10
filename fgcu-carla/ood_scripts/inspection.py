import numpy as np

# Path to the dataset
DATASET_PATH = "C:/carla_env/fgcu-carla/scripts/preprocessed/combined/combined_data.npy"

print(f"📂 Loading dataset from: {DATASET_PATH}")

# Load the dataset
try:
    data = np.load(DATASET_PATH, allow_pickle=True)
except Exception as e:
    print(f"❌ Error loading dataset: {e}")
    exit()

# Print overall dataset shape
print(f"Dataset Shape: {data.shape}")

# Check first 10 samples
for i in range(min(10, len(data))):
    print(f"Sample {i} shape: {data[i].shape if isinstance(data[i], np.ndarray) else len(data[i])}")
