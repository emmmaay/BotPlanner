import asyncio
import logging
from typing import Dict, Any, Optional
from telegram import Bot
from telegram.error import TelegramError
from config import Config
import time
from decimal import Decimal

class TelegramNotifier:
    """Handle Telegram notifications for bot activities"""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        # Reduce pool connections to prevent timeout
        self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
        self._send_delay = 0.5  # Add delay between messages
        
    async def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Send a message to the configured Telegram channel"""
        try:
            # Add delay to prevent pool timeout
            await asyncio.sleep(self._send_delay)
            
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHANNEL_ID,
                text=message,
                parse_mode=parse_mode
            )
            return True
            
        except TelegramError as e:
            # Silently fail to avoid log spam during pool issues
            return False
        except Exception as e:
            # Silently fail to avoid log spam
            return False
    
    async def notify_token_discovered(self, discovery_data: Dict[str, Any]) -> bool:
        """Notify about new fresh token discovery - CONCISE for speed"""
        try:
            token_info = discovery_data.get('token_info', {})
            token_age = discovery_data.get('token_age_minutes', 0)
            
            # Super concise for fresh tokens - speed matters!
            message = f"""
🚀 <b>FRESH TOKEN</b> ({token_age:.1f}min)
💎 {token_info.get('symbol', 'UNK')} | <code>{discovery_data['token_address'][:6]}...{discovery_data['token_address'][-4:]}</code>
🔄 Analyzing...
            """
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error notifying token discovery: {str(e)}")
            return False
    
    async def notify_security_analysis(self, token_address: str, analysis_result: Dict[str, Any]) -> bool:
        """Notify about security analysis results - CONCISE"""
        try:
            is_safe = analysis_result.get('is_safe', False)
            score = analysis_result.get('security_score', 0)
            is_fresh = analysis_result.get('is_fresh_token', False)
            
            if is_safe:
                if is_fresh:
                    message = f"✅ <b>SAFE</b> {score}% | 🚀 <b>BUYING NOW!</b>"
                else:
                    message = f"✅ <b>SAFE</b> {score}% | 🚀 <b>BUYING!</b>"
            else:
                message = f"❌ <b>UNSAFE</b> {score}% | ⛔ <b>SKIPPING</b>"
                
                # Add main risk reason
                detailed_analysis = analysis_result.get('detailed_analysis', {})
                risks = detailed_analysis.get('risks', [])
                if risks:
                    main_risk = risks[0].split(':')[0] if ':' in risks[0] else risks[0]
                    message += f"\n⚠️ {main_risk}"
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error notifying security analysis: {str(e)}")
            return False
    
    async def notify_purchase_success(
        self, 
        token_address: str, 
        token_info: Dict[str, Any], 
        buy_result: Dict[str, Any]
    ) -> bool:
        """Notify about successful token purchase - CONCISE"""
        try:
            amount_bnb = buy_result.get('amount_bnb', 0)
            tx_hash = buy_result.get('transaction_hash', '')
            
            message = f"""
🎯 <b>BOUGHT!</b> 💎 {token_info.get('symbol', 'UNK')}
💰 {amount_bnb} BNB | 🚀 <b>MOON MISSION STARTED!</b>
📝 <code>{tx_hash[:10]}...{tx_hash[-6:]}</code>
⚡ Monitoring for 5x/10x profits...
            """
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error notifying purchase success: {str(e)}")
            return False
    
    async def notify_profit_taking(
        self, 
        token_info: Dict[str, Any], 
        sale_result: Dict[str, Any],
        target: str,
        profit_percent: float
    ) -> bool:
        """Notify about profit-taking sales"""
        try:
            amount_bnb = sale_result.get('actual_bnb', 0)
            tx_hash = sale_result.get('transaction_hash', '')
            
            target_emojis = {
                '5x': '🎯',
                '10x': '💰'
            }
            
            emoji = target_emojis.get(target, '💸')
            
            message = f"""
{emoji} <b>PROFIT TAKING EXECUTED!</b> {emoji}

🎉 <b>{target.upper()} TARGET HIT!</b>
📈 <b>Profit:</b> {profit_percent:.1f}%
💰 <b>Token:</b> {token_info.get('symbol', 'UNKNOWN')}
💸 <b>BNB Received:</b> {amount_bnb}
📝 <b>TX Hash:</b> <code>{tx_hash}</code>

💎 <b>Still holding remainder for moon potential!</b> 🚀
🤖 <b>Bot continues monitoring...</b>
            """
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error notifying profit taking: {str(e)}")
            return False
    
    async def notify_error(self, error_type: str, error_message: str, token_address: str = None) -> bool:
        """Notify about errors - CONCISE"""
        try:
            # Only notify critical errors to reduce spam
            critical_errors = ['critical error', 'purchase failed', 'wallet', 'connection']
            
            if not any(critical in error_type.lower() or critical in error_message.lower() for critical in critical_errors):
                return True  # Skip non-critical errors
                
            message = f"⚠️ <b>{error_type}:</b> {error_message[:100]}..."
            
            if token_address:
                message += f"\n📊 <code>{token_address[:6]}...{token_address[-4:]}</code>"
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error notifying error: {str(e)}")
            return False
    
    async def notify_bot_status(self, status: str, details: str = "") -> bool:
        """Notify about bot status changes"""
        try:
            status_emojis = {
                'starting': '🟢',
                'running': '✅',
                'stopping': '🟡',
                'stopped': '🔴',
                'error': '⚠️'
            }
            
            emoji = status_emojis.get(status.lower(), '🤖')
            
            message = f"""
{emoji} <b>BOT STATUS UPDATE</b>

📊 <b>Status:</b> {status.upper()}
🕐 <b>Time:</b> {time.strftime('%H:%M:%S', time.localtime())}
            """
            
            if details:
                message += f"📝 <b>Details:</b> {details}"
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error notifying bot status: {str(e)}")
            return False
    
    async def notify_portfolio_summary(self, summary: Dict[str, Any]) -> bool:
        """Send portfolio summary"""
        try:
            total_invested = summary.get('total_invested_bnb', 0)
            total_value = summary.get('total_current_value_bnb', 0)
            profit_loss = summary.get('total_profit_loss_bnb', 0)
            profit_percent = summary.get('total_profit_loss_percent', 0)
            active_positions = summary.get('active_positions', 0)
            
            profit_emoji = "📈" if profit_loss > 0 else "📉"
            
            message = f"""
📊 <b>PORTFOLIO SUMMARY</b> 📊

💰 <b>Total Invested:</b> {total_invested:.4f} BNB
💎 <b>Current Value:</b> {total_value:.4f} BNB
{profit_emoji} <b>P&L:</b> {profit_loss:.4f} BNB ({profit_percent:.1f}%)
📈 <b>Active Positions:</b> {active_positions}

🕐 <b>Updated:</b> {time.strftime('%H:%M:%S', time.localtime())}
            """
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error notifying portfolio summary: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            test_message = "🤖 <b>Bot Connection Test</b>\n\n✅ Connection successful!\n🚀 Ready to hunt for gems!"
            return await self.send_message(test_message)
        except Exception as e:
            self.logger.error(f"Error testing Telegram connection: {str(e)}")
            return False

# Example usage and testing
async def test_telegram_notifier():
    """Test function for Telegram notifier"""
    notifier = TelegramNotifier()
    
    # Test connection
    success = await notifier.test_connection()
    print(f"Telegram test: {'Success' if success else 'Failed'}")

if __name__ == "__main__":
    asyncio.run(test_telegram_notifier())