import logging
import colorama
from colorama import Fore, Back, Style
import sys
import os
from datetime import datetime

# Initialize colorama
colorama.init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN, 
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE + Style.BRIGHT
    }
    
    def format(self, record):
        # Get the color for this log level
        color = self.COLORS.get(record.levelname, '')
        
        # Format the message
        formatted_message = super().format(record)
        
        # Add color if we're outputting to console
        if color and hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            formatted_message = f"{color}{formatted_message}{Style.RESET_ALL}"
        
        return formatted_message

def setup_logger(name: str = "crypto_bot", level: str = "INFO") -> logging.Logger:
    """
    Setup comprehensive logging for the crypto bot
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    
    # Convert string level to logging constant
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    log_level = level_map.get(level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create formatters
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (for real-time monitoring)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler for general logs
    log_filename = f"{logs_dir}/bot_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Error handler (separate file for errors only)
    error_filename = f"{logs_dir}/errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_filename, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    # Trading activity handler (separate file for trades)
    trade_filename = f"{logs_dir}/trades_{datetime.now().strftime('%Y%m%d')}.log"
    trade_handler = logging.FileHandler(trade_filename, encoding='utf-8')
    trade_handler.setLevel(logging.INFO)
    
    # Custom filter for trade-related logs
    class TradeFilter(logging.Filter):
        def filter(self, record):
            trade_keywords = ['buy', 'sell', 'profit', 'purchase', 'trade', 'swap', 'token']
            return any(keyword in record.getMessage().lower() for keyword in trade_keywords)
    
    trade_handler.addFilter(TradeFilter())
    trade_handler.setFormatter(file_formatter)
    logger.addHandler(trade_handler)
    
    return logger

def setup_error_handling():
    """Setup global error handling for uncaught exceptions"""
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't log keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log all other exceptions
        logger = logging.getLogger("crypto_bot")
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    # Set the exception handler
    sys.excepthook = handle_exception

class BotLogger:
    """Centralized logging utilities for the bot"""
    
    def __init__(self, name: str = "crypto_bot"):
        self.logger = setup_logger(name)
        setup_error_handling()
    
    def log_startup(self, config_summary: dict):
        """Log bot startup information"""
        self.logger.info("=" * 60)
        self.logger.info("🤖 CRYPTO SNIPING BOT STARTING UP")
        self.logger.info("=" * 60)
        self.logger.info(f"Configuration Summary:")
        for key, value in config_summary.items():
            # Mask sensitive information
            if 'key' in key.lower() or 'secret' in key.lower() or 'token' in key.lower():
                masked_value = f"{str(value)[:4]}***{str(value)[-4:]}" if len(str(value)) > 8 else "***"
                self.logger.info(f"  {key}: {masked_value}")
            else:
                self.logger.info(f"  {key}: {value}")
        self.logger.info("=" * 60)
    
    def log_shutdown(self, reason: str = "Normal shutdown"):
        """Log bot shutdown"""
        self.logger.info("=" * 60)
        self.logger.info(f"🛑 BOT SHUTTING DOWN: {reason}")
        self.logger.info("=" * 60)
    
    def log_token_discovery(self, token_address: str, discovery_type: str):
        """Log token discovery"""
        self.logger.info(f"🔍 NEW TOKEN DISCOVERED: {token_address} via {discovery_type}")
    
    def log_security_analysis(self, token_address: str, score: int, is_safe: bool):
        """Log security analysis results"""
        status = "PASSED ✅" if is_safe else "FAILED ❌"
        self.logger.info(f"🛡️ SECURITY ANALYSIS: {token_address} - Score: {score}% - {status}")
    
    def log_purchase_attempt(self, token_address: str, amount_bnb: float):
        """Log purchase attempt"""
        self.logger.info(f"🚀 PURCHASE ATTEMPT: {token_address} - Amount: {amount_bnb} BNB")
    
    def log_purchase_success(self, token_address: str, tx_hash: str, amount_bnb: float):
        """Log successful purchase"""
        self.logger.info(f"✅ PURCHASE SUCCESS: {token_address} - TX: {tx_hash} - Amount: {amount_bnb} BNB")
    
    def log_purchase_failure(self, token_address: str, error: str):
        """Log purchase failure"""
        self.logger.error(f"❌ PURCHASE FAILED: {token_address} - Error: {error}")
    
    def log_profit_taking(self, token_address: str, target: str, profit_percent: float):
        """Log profit taking execution"""
        self.logger.info(f"💰 PROFIT TAKING: {token_address} - Target: {target} - Profit: {profit_percent:.1f}%")
    
    def log_error_with_context(self, error: Exception, context: dict):
        """Log error with additional context"""
        self.logger.error(f"ERROR: {str(error)}")
        self.logger.error(f"Context: {context}")
    
    def get_logger(self) -> logging.Logger:
        """Get the underlying logger instance"""
        return self.logger

# Global logger instance
bot_logger = BotLogger()

# Convenience function to get logger
def get_logger(name: str = "crypto_bot") -> logging.Logger:
    """Get configured logger instance"""
    return logging.getLogger(name)