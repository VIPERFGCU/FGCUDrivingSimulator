import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

# Load combined dataset
DATASET_PATH = "C:/carla_env/fgcu-carla/scripts/preprocessed/combined/fixed_combined_data.npy"
OUTPUT_PATH = "C:/carla_env/fgcu-carla/scripts/models"

# Ensure output directory exists
os.makedirs(OUTPUT_PATH, exist_ok=True)

# Hyperparameters
LATENT_DIM = 20  # Compressed representation size
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 1e-3

# **VAE Model**
class VAE(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super(VAE, self).__init__()

        # Encoder
        self.fc1 = nn.Linear(input_dim, 512)
        self.fc2_mu = nn.Linear(512, latent_dim)
        self.fc2_logvar = nn.Linear(512, latent_dim)

        # Decoder
        self.fc3 = nn.Linear(latent_dim, 512)
        self.fc4 = nn.Linear(512, input_dim)

    def encode(self, x):
        h = torch.relu(self.fc1(x))
        mu = self.fc2_mu(h)
        logvar = self.fc2_logvar(h)
        return mu, logvar

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        h = torch.relu(self.fc3(z))
        return torch.sigmoid(self.fc4(h))  # Normalize output to [0,1]

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar

# **VAE Loss Function**
def vae_loss(recon_x, x, mu, logvar):
    recon_loss = nn.MSELoss()(recon_x, x)
    kl_divergence = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return recon_loss + kl_divergence

def train_vae():
    # Load dataset
    print(f"📂 Loading dataset from {DATASET_PATH}")
    data = np.load(DATASET_PATH)
    data_tensor = torch.tensor(data, dtype=torch.float32)
    
    # DataLoader
    dataset = TensorDataset(data_tensor)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # Model setup
    input_dim = data.shape[1]
    model = VAE(input_dim, LATENT_DIM)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # Training loop
    print("\n🚀 Training VAE Model...")
    model.train()
    for epoch in range(EPOCHS):
        epoch_loss = 0
        for batch in tqdm(dataloader, desc=f"🔄 Epoch {epoch+1}/{EPOCHS}"):
            x = batch[0]
            optimizer.zero_grad()
            recon_x, mu, logvar = model(x)
            loss = vae_loss(recon_x, x, mu, logvar)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        print(f"📉 Epoch {epoch+1}: Loss = {epoch_loss / len(dataloader):.4f}")

    # Save model
    model_path = os.path.join(OUTPUT_PATH, "vae_model.pth")
    torch.save(model.state_dict(), model_path)
    print(f"\n✅ VAE model saved at {model_path}")

if __name__ == "__main__":
    train_vae()
