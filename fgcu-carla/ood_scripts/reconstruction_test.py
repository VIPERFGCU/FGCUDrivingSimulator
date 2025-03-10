import torch
import os
import numpy as np
import matplotlib.pyplot as plt
from train_vae import VAE  # Ensure this matches your model definition

# 📂 Load dataset
DATASET_PATH = "C:/carla_env/fgcu-carla/scripts/preprocessed/combined/fixed_combined_data.npy"

if not os.path.exists(DATASET_PATH):
    raise FileNotFoundError(f"❌ Dataset not found at {DATASET_PATH}. Re-run combine_multimodal_data.py!")

data = np.load(DATASET_PATH, allow_pickle=True)

# **Extract Input Dimension**
input_dim = data.shape[1]  # Ensure consistency with training
latent_dim = 20  # Keep same latent dim as in train_vae.py

# **Determine the correct shape for visualization**
flattened_size = input_dim  # Total elements in one sample
side_length = int(np.sqrt(flattened_size))

# If it's not square, handle it properly
if side_length * side_length != flattened_size:
    print(f"⚠️ Warning: Data does not reshape into a square! Using full vector length ({flattened_size} elements).")
    side_length = None  # Prevent reshape error

# 🎯 Select a random subset (batch size = 10)
num_samples = 10
indices = np.random.choice(len(data), num_samples, replace=False)
input_samples = np.array([data[i] for i in indices])

# 📥 Load trained VAE model
MODEL_PATH = "C:/carla_env/fgcu-carla/scripts/models/vae_model.pth"
vae = VAE(input_dim=input_dim, latent_dim=latent_dim)  # ✅ FIXED: Pass required arguments
vae.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))
vae.eval()

# 🏗️ Convert input to tensor
input_tensor = torch.tensor(input_samples, dtype=torch.float32)

# 🔄 Pass through the VAE (Encode → Decode)
with torch.no_grad():
    reconstructed_samples, _, _ = vae(input_tensor)

# 🖼️ Plot original vs. reconstructed
fig, axes = plt.subplots(nrows=2, ncols=num_samples, figsize=(15, 4))

for i in range(num_samples):
    # Original
    if side_length:
        axes[0, i].imshow(input_samples[i].reshape(side_length, side_length), cmap="gray")  # Adjust shape
    else:
        axes[0, i].plot(input_samples[i])  # Use a line plot for non-image data
    axes[0, i].axis("off")
    axes[0, i].set_title("Original")

    # Reconstructed
    if side_length:
        axes[1, i].imshow(reconstructed_samples[i].detach().numpy().reshape(side_length, side_length), cmap="gray")
    else:
        axes[1, i].plot(reconstructed_samples[i].detach().numpy())  # Use a line plot for non-image data
    axes[1, i].axis("off")
    axes[1, i].set_title("Reconstructed")

plt.suptitle("VAE Reconstruction Test", fontsize=14)
plt.show()
