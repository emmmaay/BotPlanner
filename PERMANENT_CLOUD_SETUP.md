# 🌤️ Permanent Cloud Setup Guide - Run Your Bot Forever

## 🔑 Complete Environment Variables List

You'll need to set these **exact** environment variables on your Ubuntu server:

```bash
# Blockchain & Trading (REQUIRED)
export PRIVATE_KEY="0x9efd479d0ed30350f0ee0b581fac16edc2b4417afb14221bbd392dfca9894576"
export BSC_SCAN_API_KEY="49KJV11NHIES9X4WSH95IIN1YUJJUZ5795"

# Security Analysis (REQUIRED)  
export GOPLUS_APP_KEY="R3QUChegrrAMyXdA7MP7"
export GOPLUS_APP_SECRET="V8nZBkJgTbFYYz5gXKMkM2ASeNws4RyT"

# Telegram Notifications (REQUIRED)
export TELEGRAM_BOT_TOKEN="8364642006:AAErVG2I7gHkq7UOLf5V8VcDBhlWl4j_3kU"
export TELEGRAM_CHANNEL_ID="-1002847798463"

# Optional Trading Settings (bot uses defaults if not set)
export DEFAULT_BUY_AMOUNT="0.0001"
export GAS_RESERVE="0.0001"
export MAX_TRACKED_TOKENS="1000"
export PROFIT_TAKE_5X="25"
export PROFIT_TAKE_10X="25"
export HOLD_PERCENTAGE="50"
```

**That's ALL you need! The bot handles everything else automatically.**

---

## 🚀 Method 1: Using Screen (Easiest - Run Forever)

### Start Bot Permanently
```bash
# 1. Connect to your Ubuntu server
ssh your-server

# 2. Navigate to bot directory
cd crypto-sniping-bot

# 3. Set your environment variables (run this every time you reconnect)
export PRIVATE_KEY="your_actual_private_key"
export BSC_SCAN_API_KEY="your_actual_bsc_key"
export GOPLUS_APP_KEY="your_actual_goplus_key"
export GOPLUS_APP_SECRET="your_actual_goplus_secret"
export TELEGRAM_BOT_TOKEN="your_actual_telegram_token"
export TELEGRAM_CHANNEL_ID="your_actual_channel_id"

# 4. Activate virtual environment
source venv/bin/activate

# 5. Start bot in screen session (THIS KEEPS IT RUNNING FOREVER)
screen -S crypto_bot python3 run_bot.py
```

### Leave Terminal Without Stopping Bot
```bash
# Press these keys IN ORDER:
# Ctrl + A, then D

# Your bot keeps running even after you close your laptop/terminal!
```

### Reconnect to Running Bot
```bash
# When you want to check on your bot later:
ssh your-server
screen -r crypto_bot

# You'll see your bot running live!
```

### Stop the Bot
```bash
# Method 1: If you're connected to the screen session
Ctrl + C

# Method 2: Kill the screen session
screen -S crypto_bot -X quit

# Method 3: Find and kill the process
ps aux | grep python
kill [process_id]
```

---

## 🔄 Method 2: Systemd Service (Advanced - Auto-Restart)

This method automatically restarts your bot if it crashes and starts on server reboot.

### Create Service File
```bash
sudo nano /etc/systemd/system/crypto-bot.service
```

Add this content (replace `/home/ubuntu/` with your actual path):
```ini
[Unit]
Description=Crypto Sniping Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/crypto-sniping-bot
Environment=PATH=/home/ubuntu/crypto-sniping-bot/venv/bin
ExecStart=/home/ubuntu/crypto-sniping-bot/venv/bin/python run_bot.py
Restart=always
RestartSec=10

# Your environment variables
Environment=PRIVATE_KEY=0x9efd479d0ed30350f0ee0b581fac16edc2b4417afb14221bbd392dfca9894576
Environment=BSC_SCAN_API_KEY=49KJV11NHIES9X4WSH95IIN1YUJJUZ5795
Environment=GOPLUS_APP_KEY=R3QUChegrrAMyXdA7MP7
Environment=GOPLUS_APP_SECRET=V8nZBkJgTbFYYz5gXKMkM2ASeNws4RyT
Environment=TELEGRAM_BOT_TOKEN=8364642006:AAErVG2I7gHkq7UOLf5V8VcDBhlWl4j_3kU
Environment=TELEGRAM_CHANNEL_ID=-1002847798463

[Install]
WantedBy=multi-user.target
```

### Control Service
```bash
# Enable auto-start on boot
sudo systemctl enable crypto-bot

# Start the bot
sudo systemctl start crypto-bot

# Check status
sudo systemctl status crypto-bot

# Stop the bot
sudo systemctl stop crypto-bot

# Restart the bot
sudo systemctl restart crypto-bot

# View live logs
sudo journalctl -u crypto-bot -f
```

---

## 📱 Essential Ubuntu Commands for Your Bot

### Check if Bot is Running
```bash
# Method 1: Check screen sessions
screen -ls

# Method 2: Check processes
ps aux | grep python

# Method 3: Check systemd service (if using Method 2)
sudo systemctl status crypto-bot
```

### View Bot Logs
```bash
# Live logs (see what's happening now)
tail -f logs/bot_$(date +%Y%m%d).log

# Error logs only
tail -f logs/errors_$(date +%Y%m%d).log

# Trading activity
tail -f logs/trades_$(date +%Y%m%d).log

# All logs from today
cat logs/bot_$(date +%Y%m%d).log
```

### Monitor System Resources
```bash
# Check memory and CPU usage
htop

# Check disk space
df -h

# Check network connections
netstat -tulpn | grep python
```

### Update Your Bot (When You Make Changes)
```bash
# Stop the bot first
screen -S crypto_bot -X quit
# OR
sudo systemctl stop crypto-bot

# Pull latest changes
git pull origin main

# Restart the bot
screen -S crypto_bot python3 run_bot.py
# OR  
sudo systemctl start crypto-bot
```

---

## 🔒 Security Best Practices for Cloud

### 1. Secure Your Server
```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y

# Setup firewall (only allow SSH and your apps)
sudo ufw enable
sudo ufw allow ssh
sudo ufw status
```

### 2. Protect Your Environment Variables
```bash
# Option 1: Create a secure env file (recommended)
nano ~/crypto-bot-env.sh

# Add this content:
#!/bin/bash
export PRIVATE_KEY="your_key_here"
export BSC_SCAN_API_KEY="your_key_here"
export GOPLUS_APP_KEY="your_key_here"
export GOPLUS_APP_SECRET="your_key_here"
export TELEGRAM_BOT_TOKEN="your_key_here"
export TELEGRAM_CHANNEL_ID="your_key_here"

# Make it executable and secure
chmod 700 ~/crypto-bot-env.sh

# Use it like this:
source ~/crypto-bot-env.sh
screen -S crypto_bot python3 run_bot.py
```

### 3. Backup Your Logs and Portfolio
```bash
# Create backup script
nano backup.sh

# Add this content:
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf backups/backup_$DATE.tar.gz logs/ portfolio.json

# Run daily backup
chmod +x backup.sh
./backup.sh
```

---

## 🚨 Troubleshooting Common Issues

### Bot Stops Working
```bash
# Check if it's still running
screen -ls
ps aux | grep python

# Check logs for errors
tail -50 logs/errors_$(date +%Y%m%d).log

# Restart if needed
screen -S crypto_bot python3 run_bot.py
```

### "No module found" Error
```bash
# Make sure you're in the right directory
cd crypto-sniping-bot

# Activate virtual environment
source venv/bin/activate

# Reinstall packages if needed
pip install -r requirements.txt
```

### Telegram Not Working
```bash
# Test telegram manually
python3 -c "
import asyncio
from telegram_notifier import TelegramNotifier
asyncio.run(TelegramNotifier().test_connection())
"
```

### Low Memory Issues
```bash
# Check memory
free -h

# Add swap space if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📊 Monitoring Your Bot's Performance

### Daily Checks
```bash
# Quick health check
python3 test_bot.py

# Check wallet balance
python3 -c "
import asyncio
from trading_engine import TradingEngine
asyncio.run(TradingEngine().check_wallet_balance())
"

# View portfolio
python3 -c "
import asyncio
from portfolio_manager import PortfolioManager
from trading_engine import TradingEngine
asyncio.run(PortfolioManager(TradingEngine()).get_portfolio_summary())
"
```

### Set Up Alerts
Your bot automatically sends Telegram alerts for:
- ✅ New token discoveries
- ✅ Successful purchases  
- ✅ Profit-taking execution
- ✅ Errors and issues
- ✅ Portfolio summaries

---

## 🎯 Quick Reference Commands

```bash
# START BOT (Method 1 - Screen)
cd crypto-sniping-bot
source ~/crypto-bot-env.sh  # Load your environment variables
source venv/bin/activate
screen -S crypto_bot python3 run_bot.py
# Press Ctrl+A, then D to detach

# CHECK IF RUNNING
screen -ls

# RECONNECT TO RUNNING BOT
screen -r crypto_bot

# STOP BOT
screen -S crypto_bot -X quit

# VIEW LIVE LOGS
tail -f logs/bot_$(date +%Y%m%d).log

# CHECK SYSTEM RESOURCES
htop
```

**🚀 That's everything! Your bot will now run forever on the cloud, making you money 24/7!**