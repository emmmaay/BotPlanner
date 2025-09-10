#!/usr/bin/env python3
"""
Crypto Sniping Bot - Main Entry Point
Advanced token sniping bot with comprehensive security analysis
"""

import asyncio
import signal
import sys
import time
from typing import Dict, Any, Optional
from config import Config
from logger_setup import BotLogger
from security_analyzer import SecurityAnalyzer
from blockchain_monitor import BlockchainMonitor
from trading_engine import TradingEngine
from portfolio_manager import PortfolioManager
from telegram_notifier import TelegramNotifier

class CryptoSnipingBot:
    """Main bot orchestrator"""
    
    def __init__(self):
        self.config = Config()
        self.logger = BotLogger("CryptoSnipingBot")
        
        # Components
        self.security_analyzer = None
        self.blockchain_monitor = None
        self.trading_engine = None
        self.portfolio_manager = None
        self.telegram_notifier = None
        
        # State
        self.is_running = False
        self.purchased_tokens = set()  # Prevent duplicate purchases
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    async def initialize(self):
        """Initialize all bot components"""
        try:
            self.logger.log_startup({
                'default_buy_amount': str(self.config.DEFAULT_BUY_AMOUNT),
                'gas_reserve': str(self.config.GAS_RESERVE),
                'max_tracked_tokens': self.config.MAX_TRACKED_TOKENS,
                'bsc_rpc_url': self.config.BSC_RPC_URL,
                'pancakeswap_router': self.config.PANCAKESWAP_ROUTER
            })
            
            # Validate configuration
            self.config.validate()
            
            # Initialize components
            self.logger.get_logger().info("🔧 Initializing components...")
            
            # Telegram notifier (initialize first for error reporting)
            self.telegram_notifier = TelegramNotifier()
            await self.telegram_notifier.notify_bot_status('starting', 'Initializing components...')
            
            # Trading engine
            self.trading_engine = TradingEngine()
            
            # Portfolio manager
            self.portfolio_manager = PortfolioManager(self.trading_engine)
            
            # Security analyzer
            self.security_analyzer = SecurityAnalyzer()
            
            # Blockchain monitor (with callback)
            self.blockchain_monitor = BlockchainMonitor(
                on_new_token_callback=self._handle_new_token_discovery
            )
            
            # Test connections
            await self._test_connections()
            
            self.logger.get_logger().info("✅ All components initialized successfully")
            await self.telegram_notifier.notify_bot_status('running', 'All systems operational!')
            
        except Exception as e:
            self.logger.log_error_with_context(e, {'phase': 'initialization'})
            if self.telegram_notifier:
                await self.telegram_notifier.notify_error('Initialization', str(e))
            raise
    
    async def _test_connections(self):
        """Test all external connections"""
        self.logger.get_logger().info("🔍 Testing connections...")
        
        # Test Telegram
        telegram_ok = await self.telegram_notifier.test_connection()
        if not telegram_ok:
            raise Exception("Telegram connection failed")
        
        # Test wallet balance
        balance_info = await self.trading_engine.check_wallet_balance()
        if 'error' in balance_info:
            raise Exception(f"Wallet connection failed: {balance_info['error']}")
        
        available_balance = balance_info.get('available_for_trading', 0)
        if available_balance < float(self.config.DEFAULT_BUY_AMOUNT):
            self.logger.get_logger().warning(f"⚠️ Low balance warning: {available_balance} BNB available")
        
        self.logger.get_logger().info(f"💰 Wallet balance: {balance_info['bnb_balance']} BNB")
        self.logger.get_logger().info(f"💰 Available for trading: {available_balance} BNB")
    
    async def start(self):
        """Start the bot"""
        try:
            if self.is_running:
                self.logger.get_logger().warning("Bot is already running")
                return
            
            await self.initialize()
            self.is_running = True
            
            self.logger.get_logger().info("🚀 Starting crypto sniping bot...")
            
            # Start blockchain monitoring
            await self.blockchain_monitor.start_monitoring()
            
            # Start portfolio monitoring in background
            portfolio_task = asyncio.create_task(self.portfolio_manager.start_monitoring())
            
            # Main bot loop
            await self._main_loop()
            
        except Exception as e:
            self.logger.log_error_with_context(e, {'phase': 'startup'})
            await self._handle_critical_error(e)
        finally:
            await self.stop()
    
    async def _main_loop(self):
        """Main bot operation loop"""
        self.logger.get_logger().info("🔄 Entering main operation loop...")
        
        last_portfolio_summary = time.time()
        
        while self.is_running:
            try:
                # Send portfolio summary every hour
                if time.time() - last_portfolio_summary > 3600:  # 1 hour
                    summary = await self.portfolio_manager.get_portfolio_summary()
                    await self.telegram_notifier.notify_portfolio_summary(summary)
                    last_portfolio_summary = time.time()
                
                # Sleep to prevent high CPU usage
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.log_error_with_context(e, {'phase': 'main_loop'})
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _handle_new_token_discovery(self, discovery_data: Dict[str, Any]):
        """Handle new token discovery from blockchain monitor"""
        try:
            token_address = discovery_data['token_address']
            
            # Skip if we already processed this token
            if token_address in self.purchased_tokens:
                self.logger.get_logger().debug(f"Skipping already processed token: {token_address}")
                return
            
            self.logger.log_token_discovery(token_address, discovery_data['discovery_type'])
            
            # Notify about discovery
            await self.telegram_notifier.notify_token_discovered(discovery_data)
            
            # Perform security analysis for fresh token
            await self._analyze_and_potentially_buy(discovery_data)
            
        except Exception as e:
            self.logger.log_error_with_context(e, {
                'phase': 'token_discovery',
                'token_address': discovery_data.get('token_address', 'unknown')
            })
            await self.telegram_notifier.notify_error(
                'Token Discovery',
                str(e),
                discovery_data.get('token_address')
            )
    
    async def _analyze_and_potentially_buy(self, discovery_data: Dict[str, Any]):
        """Analyze token security and buy if it passes all checks"""
        try:
            token_address = discovery_data['token_address']
            token_info = discovery_data['token_info']
            
            self.logger.get_logger().info(f"🔍 Starting security analysis for {token_address}")
            
            # Perform comprehensive security analysis for fresh token
            is_fresh_token = discovery_data.get('is_fresh', False)
            async with self.security_analyzer:
                analysis_result = await self.security_analyzer.analyze_token_security(
                    token_address, 
                    is_fresh_token=is_fresh_token
                )
            
            is_safe = analysis_result.get('is_safe', False)
            score = analysis_result.get('security_score', 0)
            
            self.logger.log_security_analysis(token_address, score, is_safe)
            
            # Notify about analysis results
            await self.telegram_notifier.notify_security_analysis(token_address, analysis_result)
            
            if is_safe:
                # Token passed security checks - attempt purchase
                await self._attempt_purchase(token_address, token_info, analysis_result)
            else:
                self.logger.get_logger().info(f"❌ Token {token_address} failed security checks (Score: {score}%)")
                
        except Exception as e:
            self.logger.log_error_with_context(e, {
                'phase': 'security_analysis',
                'token_address': discovery_data.get('token_address', 'unknown')
            })
            await self.telegram_notifier.notify_error(
                'Security Analysis',
                str(e),
                discovery_data.get('token_address')
            )
    
    async def _attempt_purchase(
        self, 
        token_address: str, 
        token_info: Dict[str, Any], 
        analysis_result: Dict[str, Any]
    ):
        """Attempt to purchase a token that passed security analysis"""
        try:
            # Mark as processed to prevent duplicates
            self.purchased_tokens.add(token_address)
            
            self.logger.log_purchase_attempt(token_address, float(self.config.DEFAULT_BUY_AMOUNT))
            
            # Execute purchase
            buy_result = await self.trading_engine.buy_token(
                token_address=token_address,
                amount_bnb=self.config.DEFAULT_BUY_AMOUNT,
                slippage_percent=12.0
            )
            
            if buy_result['success']:
                # Purchase successful
                self.logger.log_purchase_success(
                    token_address,
                    buy_result['transaction_hash'],
                    buy_result['amount_bnb']
                )
                
                # Add to portfolio
                await self.portfolio_manager.add_position(token_address, token_info, buy_result)
                
                # Send celebration notification
                await self.telegram_notifier.notify_purchase_success(
                    token_address, token_info, buy_result
                )
                
            else:
                # Purchase failed
                error_msg = buy_result.get('error', 'Unknown error')
                self.logger.log_purchase_failure(token_address, error_msg)
                
                await self.telegram_notifier.notify_error(
                    'Purchase Failed',
                    error_msg,
                    token_address
                )
                
                # Remove from processed set so we can retry if needed
                self.purchased_tokens.discard(token_address)
                
        except Exception as e:
            self.logger.log_error_with_context(e, {
                'phase': 'purchase_attempt',
                'token_address': token_address
            })
            await self.telegram_notifier.notify_error(
                'Purchase Error',
                str(e),
                token_address
            )
            # Remove from processed set on error
            self.purchased_tokens.discard(token_address)
    
    async def _handle_critical_error(self, error: Exception):
        """Handle critical errors that might require bot restart"""
        self.logger.get_logger().critical(f"💥 CRITICAL ERROR: {str(error)}")
        
        if self.telegram_notifier:
            await self.telegram_notifier.notify_error('Critical Error', str(error))
            await self.telegram_notifier.notify_bot_status('error', f'Critical error: {str(error)}')
        
        # In a production environment, you might want to implement
        # automatic restart logic here
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.get_logger().info(f"📢 Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(self.stop())
    
    async def stop(self):
        """Stop the bot gracefully"""
        if not self.is_running:
            return
        
        self.logger.get_logger().info("🛑 Stopping crypto sniping bot...")
        self.is_running = False
        
        try:
            # Stop monitoring
            if self.blockchain_monitor:
                self.blockchain_monitor.stop_monitoring()
            
            # Send final notifications
            if self.telegram_notifier:
                await self.telegram_notifier.notify_bot_status('stopped', 'Bot shutdown complete')
            
            # Get final portfolio summary
            if self.portfolio_manager:
                summary = await self.portfolio_manager.get_portfolio_summary()
                if self.telegram_notifier:
                    await self.telegram_notifier.notify_portfolio_summary(summary)
            
        except Exception as e:
            self.logger.log_error_with_context(e, {'phase': 'shutdown'})
        
        self.logger.log_shutdown("Graceful shutdown completed")

async def main():
    """Main entry point"""
    bot = CryptoSnipingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)