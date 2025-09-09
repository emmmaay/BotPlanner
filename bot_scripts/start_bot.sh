#!/bin/bash
# Quick start script for crypto sniping bot

echo "🤖 Starting Crypto Sniping Bot..."
echo "================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./ubuntu_setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if environment variables are set
if [ -z "$PRIVATE_KEY" ] || [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️ Environment variables not set!"
    echo ""
    echo "Please set your environment variables first:"
    echo "export PRIVATE_KEY='your_private_key'"
    echo "export BSC_SCAN_API_KEY='your_bsc_scan_api_key'"
    echo "export GOPLUS_APP_KEY='your_goplus_app_key'"
    echo "export GOPLUS_APP_SECRET='your_goplus_app_secret'"
    echo "export TELEGRAM_BOT_TOKEN='your_telegram_bot_token'"
    echo "export TELEGRAM_CHANNEL_ID='your_telegram_channel_id'"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Test components first
echo "🧪 Testing bot components..."
python3 bot_scripts/test_bot.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🚀 All tests passed! Starting bot in screen session..."
    echo ""
    echo "The bot will run in background. Use these commands:"
    echo "  screen -r crypto_bot  (to reconnect)"
    echo "  screen -ls           (to list sessions)"
    echo "  Ctrl+A then D        (to detach without stopping)"
    echo ""
    
    # Start bot in screen session
    screen -S crypto_bot python3 bot_scripts/run_bot.py
else
    echo "❌ Tests failed. Please check your configuration."
    exit 1
fi