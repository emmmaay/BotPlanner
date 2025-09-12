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
    
    # ====================================================================
    # 🎯 YOUR TRADING SETTINGS - CHANGE THESE ANYTIME YOU WANT!
    # ====================================================================
    # Your current balance: 0.0004 BNB
    # Gas cost per trade: ~0.0025 BNB 
    # 
    # RECOMMENDED FOR YOUR BALANCE:
    # - Buy amount: 0.00001 BNB ($0.06) per token  
    # - Gas reserve: Keep 0.0035 BNB for gas
    # - This gives you: 0.0004 - 0.0035 = Not enough! Need more BNB!
    #
    # OPTION 1: Add more BNB to wallet (recommended: at least 0.01 BNB)
    # OPTION 2: Try tiny amounts (risk: may not be profitable)
    # ====================================================================
    
    DEFAULT_BUY_AMOUNT = Decimal(os.getenv('DEFAULT_BUY_AMOUNT', '0.000008'))  # Super tiny for testing
    GAS_RESERVE = Decimal(os.getenv('GAS_RESERVE', '0.000350'))  # Gas reserve
    MIN_WALLET_BALANCE = Decimal(os.getenv('MIN_WALLET_BALANCE', '0.000350'))  # Never go below this
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
    
    # Security thresholds for fresh tokens (sniping mode)
    MIN_LIQUIDITY_USD = 500  # Lower for fresh tokens
    MAX_HOLDER_PERCENTAGE = 50  # Higher tolerance for new tokens
    MIN_HOLDERS_COUNT = 1  # Allow very new tokens
    HONEYPOT_CHECK = True
    
    # Fresh token sniping configuration
    MAX_TOKEN_AGE_MINUTES = 3  # Only snipe tokens max 3 minutes old
    FRESH_TOKEN_SECURITY_THRESHOLD = 60  # Lower threshold for fresh tokens
    MIN_LIQUIDITY_FRESH_USD = 100  # Minimum liquidity for fresh tokens
    
    # Denylist of known old tokens (DO NOT SNIPE THESE!)
    DENYLIST_TOKENS = [
        '0x55d398326f99059fF775485246999027B3197955',  # USDT
        '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',  # BUSD  
        '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',  # USDC
        '0xbb4CdB9CBd36B01bD1cBaeBF2De08d9173bc095c',  # WBNB
        '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',  # CAKE
        '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',  # BTCB
        '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',  # ETH
    ]
    
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