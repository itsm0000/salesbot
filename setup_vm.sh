
#!/bin/bash

# Setup Script for Muntazir on Google Cloud VM (Debian/Ubuntu)
# Usage: ./setup_vm.sh

echo "🚀 Starting Muntazir VM Setup..."

# 1. Update System
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker & Compose
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    echo "⚠️  You might need to log out and back in for Docker group changes to take effect."
else
    echo "✅ Docker already installed."
fi

# 3. Setup Project Directory (Assuming code is already copied or cloned here)
echo "📂 Setting up project..."

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Creating from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "❗ Please edit .env with your actual API Keys before running!"
    else
        echo "❌ .env.example missing. Please ensure project files are complete."
    fi
fi

# 4. Build and Run
echo "🚀 Building and deploying Container..."
# Use docker compose plugin (v2) or docker-compose (v1)
if command -v docker-compose &> /dev/null; then
    sudo docker-compose up -d --build
else
    sudo docker compose up -d --build
fi

echo "✅ Deployment complete! Muntazir should be running on port 8000."
echo "   Test with: curl http://localhost:8000/api/health"
