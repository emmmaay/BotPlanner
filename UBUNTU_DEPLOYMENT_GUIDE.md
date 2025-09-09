# 🤖 Crypto Sniping Bot - Ubuntu Deployment Guide

## Quick Start (5 Minutes Setup)

### 1. 📥 Clone Repository on Ubuntu Server
```bash
git clone <your-repository-url>
cd crypto-sniping-bot
```

### 2. 🔧 Run Automated Setup
```bash
# Make setup script executable
chmod +x ubuntu_setup.sh

# Run setup (installs Python 3.11, dependencies, etc.)
./ubuntu_setup.sh
```

### 3. 🔑 Set Environment Variables
```bash
# Set your credentials (replace with your actual values)
export PRIVATE_KEY="your_private_key_here"
export BSC_SCAN_API_KEY="your_bsc_scan_api_key"
export GOPLUS_APP_KEY="your_goplus_app_key"
export GOPLUS_APP_SECRET="your_goplus_app_secret"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHANNEL_ID="your_telegram_channel_id"
```

### 4. 🧪 Test Everything
```bash
# Activate virtual environment
source venv/bin/activate

# Test all components
python3 test_bot.py
```

### 5. 🚀 Run the Bot
```bash
# Option 1: Run directly
python3 run_bot.py

# Option 2: Run in background with screen
screen -S crypto_bot python3 run_bot.py
# Press Ctrl+A, then D to detach from screen
# Use 'screen -r crypto_bot' to reattach
```

---

## 📋 Detailed Setup Instructions

### System Requirements
- Ubuntu 20.04+ (recommended)
- Python 3.11
- 1GB+ RAM
- Stable internet connection
- At least 0.01 BNB in wallet for gas fees

### Manual Installation Steps

#### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Install Python 3.11
```bash
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-pip python3.11-venv python3.11-dev
```

#### 3. Install System Dependencies
```bash
sudo apt install -y git curl wget build-essential libssl-dev libffi-dev screen htop
```

#### 4. Setup Project
```bash
# Clone repository
git clone <your-repository-url>
cd crypto-sniping-bot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Set permissions
chmod +x run_bot.py
chmod +x ubuntu_setup.sh
```

#### 5. Configure Environment Variables
Create a `.env` file or export variables:

```bash
# Option 1: Create .env file (not recommended for production)
nano .env
# Add your variables

# Option 2: Export variables (recommended)
export PRIVATE_KEY="0x..."
export BSC_SCAN_API_KEY="..."
export GOPLUS_APP_KEY="..."
export GOPLUS_APP_SECRET="..."
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHANNEL_ID="..."
```

#### 6. Test Installation
```bash
# Test configuration
python3 -c "from config import Config; Config.validate(); print('✅ Config OK')"

# Test all components
python3 test_bot.py
```

#### 7. Run Bot
```bash
python3 run_bot.py
```

---

## 🛠️ Configuration Options

### Trading Configuration (Optional)
You can customize these in your environment:

```bash
export DEFAULT_BUY_AMOUNT="0.0001"  # BNB amount per purchase
export GAS_RESERVE="0.0001"         # BNB to keep for gas
export MAX_TRACKED_TOKENS="1000"    # Max tokens to monitor
export PROFIT_TAKE_5X="25"          # % to sell at 5x profit
export PROFIT_TAKE_10X="25"         # % to sell at 10x profit
export HOLD_PERCENTAGE="50"         # % to hold long-term
```

---

## 🔄 Running in Background

### Using Screen (Recommended)
```bash
# Start bot in screen session
screen -S crypto_bot python3 run_bot.py

# Detach from screen (Ctrl+A, then D)
# Reattach to screen
screen -r crypto_bot

# List screen sessions
screen -ls
```

### Using systemd (Advanced)
Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/crypto-bot.service
```

Add this content:
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

# Add your environment variables here
Environment=PRIVATE_KEY=your_key_here
Environment=BSC_SCAN_API_KEY=your_key_here
# ... add all other variables

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable crypto-bot
sudo systemctl start crypto-bot
sudo systemctl status crypto-bot
```

---

## 📊 Monitoring & Logs

### View Logs
```bash
# Real-time logs
tail -f logs/bot_$(date +%Y%m%d).log

# Error logs only
tail -f logs/errors_$(date +%Y%m%d).log

# Trading activity
tail -f logs/trades_$(date +%Y%m%d).log
```

### System Monitoring
```bash
# Check system resources
htop

# Check bot process
ps aux | grep python

# Check network connections
netstat -tulpn | grep python
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. Permission denied errors
```bash
# Set correct permissions
chmod +x run_bot.py
chmod +x ubuntu_setup.sh
```

#### 3. Telegram connection fails
- Verify TELEGRAM_BOT_TOKEN is correct
- Ensure bot is added to your channel
- Check TELEGRAM_CHANNEL_ID format (should start with -)

#### 4. Wallet connection fails
- Verify PRIVATE_KEY is correct (should start with 0x)
- Ensure wallet has BNB for gas fees
- Check BSC RPC endpoint is accessible

#### 5. Low memory issues
```bash
# Check memory usage
free -h

# Add swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Getting Help
1. Check logs in `logs/` directory
2. Run `python3 test_bot.py` to diagnose issues
3. Ensure all environment variables are set correctly

---

## 🚀 Performance Tips

### Optimize for Speed
1. Use a VPS close to BSC nodes (Singapore/US)
2. Ensure stable, fast internet connection
3. Monitor system resources regularly
4. Keep only essential processes running

### Security Best Practices
1. Never commit private keys to git
2. Use environment variables for all secrets
3. Regularly update system packages
4. Monitor bot activity through Telegram notifications
5. Keep logs for audit trails

---

## 📈 Expected Bot Behavior

Once running, your bot will:

1. 🔍 **Monitor blockchain** for new token launches
2. 🛡️ **Analyze security** using 30+ checks via Go Plus API
3. 💰 **Buy tokens** that pass all security criteria
4. 📱 **Send notifications** to your Telegram channel
5. 📊 **Track portfolio** and execute profit-taking automatically
6. 🌙 **Hold 50%** of each position for moon potential

### Sample Telegram Messages
```
🔍 NEW TOKEN DISCOVERED!
💎 Token: SafeMoon2.0 (SAFE2)
📊 Address: 0x...
🔄 Running security analysis...

✅ SECURITY ANALYSIS COMPLETE
🛡️ Security Score: 85%
🚀 Token meets security criteria! Preparing to purchase...

🎉 MOONSHOT ACQUIRED! 🚀
💰 Token: SafeMoon2.0 (SAFE2)
💸 Amount Invested: 0.0001 BNB
📝 TX Hash: 0x...
🚀 TO THE MOON! 🌙
```

---

🎯 **Your bot is now ready to hunt for the next 100x gem!**