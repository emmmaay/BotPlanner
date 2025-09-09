#!/usr/bin/env python3
"""
Run script for the crypto sniping bot
This script handles startup, error recovery, and environment setup
"""

import asyncio
import sys
import os
import signal
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from main_bot import CryptoSnipingBot

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'PRIVATE_KEY', 'BSC_SCAN_API_KEY', 'GOPLUS_APP_KEY', 
        'GOPLUS_APP_SECRET', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running the bot.")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    """Main entry point"""
    print("🤖 Crypto Sniping Bot - Starting Up...")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    try:
        # Run the bot
        asyncio.run(CryptoSnipingBot().start())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()