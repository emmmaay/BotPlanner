#!/usr/bin/env python3
"""
Test script for crypto sniping bot components
"""

import asyncio
import sys
from config import Config
from telegram_notifier import TelegramNotifier
from trading_engine import TradingEngine

async def test_all_components():
    """Test all bot components"""
    print("🤖 Testing Crypto Sniping Bot Components")
    print("=" * 50)
    
    try:
        # Test configuration
        print("🔧 Testing configuration...")
        config = Config()
        config.validate()
        print("✅ Configuration validated successfully")
        
        # Test Telegram
        print("📱 Testing Telegram connection...")
        notifier = TelegramNotifier()
        telegram_ok = await notifier.test_connection()
        if telegram_ok:
            print("✅ Telegram connection successful")
        else:
            print("❌ Telegram connection failed")
            return False
        
        # Test trading engine (wallet connection)
        print("💰 Testing wallet connection...")
        trading_engine = TradingEngine()
        balance_info = await trading_engine.check_wallet_balance()
        
        if 'error' not in balance_info:
            print(f"✅ Wallet connected - Balance: {balance_info['bnb_balance']} BNB")
            print(f"💰 Available for trading: {balance_info['available_for_trading']} BNB")
        else:
            print(f"❌ Wallet connection failed: {balance_info['error']}")
            return False
        
        print("\n🎉 All component tests passed!")
        print("🚀 Your bot is ready to start hunting for gems!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_all_components())
    sys.exit(0 if success else 1)