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
        self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
        
    async def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Send a message to the configured Telegram channel"""
        try:
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHANNEL_ID,
                text=message,
                parse_mode=parse_mode
            )
            self.logger.info("✅ Telegram message sent successfully")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Telegram error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {str(e)}")
            return False
    
    async def notify_token_discovered(self, discovery_data: Dict[str, Any]) -> bool:
        """Notify about new token discovery"""
        try:
            token_info = discovery_data.get('token_info', {})
            
            message = f"""
🔍 <b>NEW TOKEN DISCOVERED!</b>

💎 <b>Token:</b> {token_info.get('name', 'Unknown')} ({token_info.get('symbol', 'UNKNOWN')})
📊 <b>Address:</b> <code>{discovery_data['token_address']}</code>
🔗 <b>Pair:</b> <code>{discovery_data['pair_address']}</code>
⚡ <b>Discovery:</b> {discovery_data['discovery_type'].replace('_', ' ').title()}
⛽ <b>Block:</b> {discovery_data['block_number']}
🕐 <b>Time:</b> {time.strftime('%H:%M:%S', time.localtime(discovery_data['timestamp']))}

🔄 Running security analysis...
            """
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error notifying token discovery: {str(e)}")
            return False
    
    async def notify_security_analysis(self, token_address: str, analysis_result: Dict[str, Any]) -> bool:
        """Notify about security analysis results"""
        try:
            is_safe = analysis_result.get('is_safe', False)
            score = analysis_result.get('security_score', 0)
            
            if is_safe:
                status_emoji = "✅"
                status_text = "PASSED SECURITY"
            else:
                status_emoji = "❌"
                status_text = "FAILED SECURITY"
            
            message = f"""
{status_emoji} <b>SECURITY ANALYSIS COMPLETE</b>

📊 <b>Token:</b> <code>{token_address}</code>
🛡️ <b>Security Score:</b> {score}%
📋 <b>Status:</b> {status_text}

            """
            
            if is_safe:
                message += "🚀 <b>Token meets security criteria! Preparing to purchase...</b>"
            else:
                # Add risk details
                detailed_analysis = analysis_result.get('detailed_analysis', {})
                risks = detailed_analysis.get('risks', [])
                if risks:
                    message += "⚠️ <b>Security Issues:</b>\n"
                    for risk in risks[:3]:  # Show top 3 risks
                        message += f"• {risk}\n"
            
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
        """Notify about successful token purchase with sweet celebration"""
        try:
            amount_bnb = buy_result.get('amount_bnb', 0)
            tx_hash = buy_result.get('transaction_hash', '')
            actual_tokens = buy_result.get('actual_tokens', 0)
            
            # Sweet celebration messages
            celebration_messages = [
                "🎉 MOONSHOT ACQUIRED! 🚀",
                "💎 DIAMOND HANDS ACTIVATED! 💎", 
                "🔥 ABSOLUTE GEM SECURED! 🔥",
                "⚡ LIGHTNING FAST SNIPE! ⚡",
                "🎯 BULLSEYE TARGET HIT! 🎯",
                "🏆 CHAMPION MOVE EXECUTED! 🏆"
            ]
            
            import random
            celebration = random.choice(celebration_messages)
            
            message = f"""
{celebration}

🎊 <b>SUCCESSFUL PURCHASE!</b> 🎊

💰 <b>Token:</b> {token_info.get('name', 'Unknown')} ({token_info.get('symbol', 'UNKNOWN')})
📊 <b>Address:</b> <code>{token_address}</code>
💸 <b>Amount Invested:</b> {amount_bnb} BNB
🪙 <b>Tokens Received:</b> {actual_tokens:,}
📝 <b>TX Hash:</b> <code>{tx_hash}</code>

🚀 <b>TO THE MOON!</b> 🌙
💎 <b>Hold tight, this one's going places!</b>

⚡ Profit targets:
• 25% at 5x (500% gain)
• 25% at 10x (1000% gain)  
• 50% riding to the moon! 🌙

🤖 Bot is now monitoring for profit opportunities...
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
        """Notify about errors"""
        try:
            message = f"""
⚠️ <b>BOT ERROR ALERT</b> ⚠️

🔴 <b>Error Type:</b> {error_type}
📝 <b>Message:</b> {error_message}
            """
            
            if token_address:
                message += f"📊 <b>Token:</b> <code>{token_address}</code>\n"
            
            message += f"🕐 <b>Time:</b> {time.strftime('%H:%M:%S', time.localtime())}"
            
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