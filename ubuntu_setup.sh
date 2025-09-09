#!/bin/bash
# Ubuntu Setup Script for Crypto Sniping Bot
# Run this script on your Ubuntu server to set up the bot

echo "🤖 Setting up Crypto Sniping Bot on Ubuntu"
echo "=========================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 if not available
echo "🐍 Installing Python 3.11..."
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-pip python3.11-venv python3.11-dev

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    screen \
    htop

# Create virtual environment
echo "🔧 Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Set permissions
echo "🔒 Setting permissions..."
chmod +x run_bot.py
chmod +x ubuntu_setup.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set your environment variables:"
echo "   export PRIVATE_KEY='your_private_key'"
echo "   export BSC_SCAN_API_KEY='your_bsc_scan_api_key'"
echo "   export GOPLUS_APP_KEY='your_goplus_app_key'"
echo "   export GOPLUS_APP_SECRET='your_goplus_app_secret'"
echo "   export TELEGRAM_BOT_TOKEN='your_telegram_bot_token'"
echo "   export TELEGRAM_CHANNEL_ID='your_telegram_channel_id'"
echo ""
echo "2. Run the bot:"
echo "   python3.11 run_bot.py"
echo ""
echo "3. Or run in background with screen:"
echo "   screen -S crypto_bot python3.11 run_bot.py"
echo ""
echo "🚀 Ready to snipe some tokens!"