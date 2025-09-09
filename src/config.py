import os
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()

class Config:
    # Blockchain Configuration
    PRIVATE_KEY = os.getenv('PRIVATE_KEY', '')
    BSC_RPC_URL = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed.binance.org/')
    BSC_SCAN_API_KEY = os.getenv('BSC_SCAN_API_KEY', '')
    
    # Go Plus API Configuration
    GOPLUS_APP_KEY = os.getenv('GOPLUS_APP_KEY', '')
    GOPLUS_APP_SECRET = os.getenv('GOPLUS_APP_SECRET', '')
    GOPLUS_BASE_URL = 'https://api.gopluslabs.io'
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '')
    
    # Trading Configuration
    DEFAULT_BUY_AMOUNT = Decimal(os.getenv('DEFAULT_BUY_AMOUNT', '0.0001'))
    GAS_RESERVE = Decimal(os.getenv('GAS_RESERVE', '0.0001'))
    MAX_TRACKED_TOKENS = int(os.getenv('MAX_TRACKED_TOKENS', '1000'))
    PROFIT_TAKE_5X = int(os.getenv('PROFIT_TAKE_5X', '25'))
    PROFIT_TAKE_10X = int(os.getenv('PROFIT_TAKE_10X', '25'))
    HOLD_PERCENTAGE = int(os.getenv('HOLD_PERCENTAGE', '50'))
    
    # PancakeSwap Configuration  
    PANCAKESWAP_ROUTER = os.getenv('PANCAKESWAP_ROUTER', '0x10ED43C718714eb63d5aA57B78B54704E256024E')
    PANCAKESWAP_FACTORY = os.getenv('PANCAKESWAP_FACTORY', '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73')
    WBNB_ADDRESS = os.getenv('WBNB_ADDRESS', '0xbb4CdB9CBd36B01bD1cBaeBF2De08d9173bc095c')
    
    # BSC Chain ID
    BSC_CHAIN_ID = 56
    
    # Security thresholds
    MIN_LIQUIDITY_USD = 1000
    MAX_HOLDER_PERCENTAGE = 30
    MIN_HOLDERS_COUNT = 5
    HONEYPOT_CHECK = True
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set"""
        required_vars = [
            'PRIVATE_KEY', 'BSC_SCAN_API_KEY', 'GOPLUS_APP_KEY', 
            'GOPLUS_APP_SECRET', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True