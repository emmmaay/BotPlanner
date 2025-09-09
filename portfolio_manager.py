import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional
from decimal import Decimal
from dataclasses import dataclass, asdict
from config import Config
from trading_engine import TradingEngine

@dataclass
class TokenPosition:
    """Represents a token position in the portfolio"""
    token_address: str
    token_name: str
    token_symbol: str
    amount_tokens: int
    amount_bnb_invested: Decimal
    buy_price_bnb: Decimal
    buy_timestamp: int
    buy_tx_hash: str
    current_price_bnb: Optional[Decimal] = None
    profit_loss_percent: Optional[float] = None
    profit_loss_bnb: Optional[Decimal] = None
    is_monitoring: bool = True
    partial_sales: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.partial_sales is None:
            self.partial_sales = []

class PortfolioManager:
    """Manage token portfolio and automated profit-taking"""
    
    def __init__(self, trading_engine: TradingEngine):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.trading_engine = trading_engine
        
        # Portfolio tracking
        self.positions: Dict[str, TokenPosition] = {}
        self.portfolio_file = "portfolio.json"
        
        # Profit-taking configuration
        self.profit_targets = {
            '5x': self.config.PROFIT_TAKE_5X,   # 25% at 5x
            '10x': self.config.PROFIT_TAKE_10X  # 25% at 10x
        }
        
        # Load existing portfolio
        self._load_portfolio()
        
        self.logger.info(f"Portfolio manager initialized with {len(self.positions)} positions")
    
    def _load_portfolio(self):
        """Load portfolio from file"""
        try:
            with open(self.portfolio_file, 'r') as f:
                data = json.load(f)
                for token_addr, position_data in data.items():
                    # Convert back to TokenPosition object
                    position = TokenPosition(**position_data)
                    self.positions[token_addr] = position
                    
            self.logger.info(f"Loaded {len(self.positions)} positions from portfolio file")
            
        except FileNotFoundError:
            self.logger.info("No existing portfolio file found, starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading portfolio: {str(e)}")
    
    def _save_portfolio(self):
        """Save portfolio to file"""
        try:
            # Convert positions to serializable format
            data = {}
            for token_addr, position in self.positions.items():
                position_dict = asdict(position)
                # Convert Decimal to string for JSON serialization
                position_dict['amount_bnb_invested'] = str(position_dict['amount_bnb_invested'])
                position_dict['buy_price_bnb'] = str(position_dict['buy_price_bnb'])
                if position_dict['current_price_bnb']:
                    position_dict['current_price_bnb'] = str(position_dict['current_price_bnb'])
                if position_dict['profit_loss_bnb']:
                    position_dict['profit_loss_bnb'] = str(position_dict['profit_loss_bnb'])
                    
                data[token_addr] = position_dict
            
            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving portfolio: {str(e)}")
    
    async def add_position(
        self, 
        token_address: str, 
        token_info: Dict[str, Any], 
        buy_result: Dict[str, Any]
    ) -> bool:
        """Add a new token position to portfolio"""
        try:
            if token_address in self.positions:
                self.logger.warning(f"Position for {token_address} already exists")
                return False
            
            # Check if we're at max capacity
            if len(self.positions) >= self.config.MAX_TRACKED_TOKENS:
                self.logger.warning(f"Portfolio at max capacity ({self.config.MAX_TRACKED_TOKENS} tokens)")
                return False
            
            # Create new position
            position = TokenPosition(
                token_address=token_address,
                token_name=token_info.get('name', 'Unknown'),
                token_symbol=token_info.get('symbol', 'UNKNOWN'),
                amount_tokens=buy_result.get('actual_tokens', 0),
                amount_bnb_invested=Decimal(str(buy_result['amount_bnb'])),
                buy_price_bnb=Decimal(str(buy_result['amount_bnb'])) / Decimal(str(buy_result.get('actual_tokens', 1))),
                buy_timestamp=buy_result['timestamp'],
                buy_tx_hash=buy_result['transaction_hash']
            )
            
            self.positions[token_address] = position
            self._save_portfolio()
            
            self.logger.info(f"✅ Added new position: {position.token_symbol} ({token_address})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding position: {str(e)}")
            return False
    
    async def update_prices(self):
        """Update current prices for all positions"""
        try:
            for token_address, position in self.positions.items():
                if not position.is_monitoring:
                    continue
                
                try:
                    # Get current price
                    current_price = await self.trading_engine.get_token_price_bnb(
                        token_address, 
                        position.amount_tokens
                    )
                    
                    if current_price:
                        position.current_price_bnb = current_price
                        
                        # Calculate profit/loss
                        current_value = current_price * Decimal(str(position.amount_tokens))
                        invested_value = position.amount_bnb_invested
                        
                        position.profit_loss_bnb = current_value - invested_value
                        position.profit_loss_percent = float(
                            (position.profit_loss_bnb / invested_value) * 100
                        )
                        
                        # Check for profit-taking opportunities
                        await self._check_profit_taking(token_address, position)
                        
                except Exception as e:
                    self.logger.error(f"Error updating price for {token_address}: {str(e)}")
                    continue
            
            # Save updated portfolio
            self._save_portfolio()
            
        except Exception as e:
            self.logger.error(f"Error updating prices: {str(e)}")
    
    async def _check_profit_taking(self, token_address: str, position: TokenPosition):
        """Check if position meets profit-taking criteria"""
        try:
            if not position.profit_loss_percent:
                return
            
            profit_percent = position.profit_loss_percent
            
            # Check 5x profit target (500% gain)
            if profit_percent >= 500 and not self._already_sold_at_target(position, '5x'):
                await self._execute_profit_taking(token_address, position, '5x', 500)
            
            # Check 10x profit target (1000% gain)
            elif profit_percent >= 1000 and not self._already_sold_at_target(position, '10x'):
                await self._execute_profit_taking(token_address, position, '10x', 1000)
                
        except Exception as e:
            self.logger.error(f"Error checking profit taking for {token_address}: {str(e)}")
    
    def _already_sold_at_target(self, position: TokenPosition, target: str) -> bool:
        """Check if we've already sold at this profit target"""
        for sale in position.partial_sales:
            if sale.get('target') == target:
                return True
        return False
    
    async def _execute_profit_taking(
        self, 
        token_address: str, 
        position: TokenPosition, 
        target: str, 
        profit_percent: float
    ):
        """Execute profit-taking sale"""
        try:
            # Calculate amount to sell based on target
            sell_percentage = self.profit_targets[target]
            total_tokens = position.amount_tokens
            
            # Account for previous sales
            total_sold = sum(sale.get('amount_tokens', 0) for sale in position.partial_sales)
            remaining_tokens = total_tokens - total_sold
            
            if remaining_tokens <= 0:
                self.logger.warning(f"No tokens remaining to sell for {position.token_symbol}")
                return
            
            # Calculate tokens to sell (percentage of original position, not remaining)
            tokens_to_sell = int((total_tokens * sell_percentage) / 100)
            tokens_to_sell = min(tokens_to_sell, remaining_tokens)  # Don't sell more than we have
            
            self.logger.info(f"🎯 Executing {target} profit-taking for {position.token_symbol}: "
                           f"selling {tokens_to_sell} tokens ({sell_percentage}%) at {profit_percent:.1f}% profit")
            
            # Execute sell order
            sell_result = await self.trading_engine.sell_token(
                token_address=token_address,
                amount_tokens=tokens_to_sell,
                slippage_percent=15.0  # Higher slippage for profit-taking
            )
            
            if sell_result['success']:
                # Record the sale
                sale_record = {
                    'target': target,
                    'profit_percent': profit_percent,
                    'amount_tokens': tokens_to_sell,
                    'amount_bnb_received': sell_result.get('actual_bnb', 0),
                    'timestamp': int(time.time()),
                    'tx_hash': sell_result['transaction_hash']
                }
                
                position.partial_sales.append(sale_record)
                
                # If we've sold both 5x and 10x portions, stop monitoring
                if len(position.partial_sales) >= 2:
                    position.is_monitoring = False
                    self.logger.info(f"🏁 Completed all profit-taking for {position.token_symbol}. "
                                   f"Holding remaining {self.config.HOLD_PERCENTAGE}% for moon potential")
                
                self._save_portfolio()
                
                self.logger.info(f"✅ Profit-taking successful: {sell_result}")
                return sell_result
            else:
                self.logger.error(f"❌ Profit-taking failed: {sell_result}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error executing profit-taking: {str(e)}")
            return None
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary with current values"""
        try:
            await self.update_prices()
            
            total_invested = Decimal('0')
            total_current_value = Decimal('0')
            active_positions = 0
            completed_positions = 0
            
            position_summaries = []
            
            for token_address, position in self.positions.items():
                total_invested += position.amount_bnb_invested
                
                if position.current_price_bnb and position.amount_tokens > 0:
                    # Calculate remaining tokens
                    sold_tokens = sum(sale.get('amount_tokens', 0) for sale in position.partial_sales)
                    remaining_tokens = position.amount_tokens - sold_tokens
                    
                    current_value = position.current_price_bnb * Decimal(str(remaining_tokens))
                    total_current_value += current_value
                
                if position.is_monitoring:
                    active_positions += 1
                else:
                    completed_positions += 1
                
                # Add to summaries
                position_summaries.append({
                    'token_address': token_address,
                    'symbol': position.token_symbol,
                    'name': position.token_name,
                    'invested_bnb': float(position.amount_bnb_invested),
                    'profit_loss_percent': position.profit_loss_percent,
                    'profit_loss_bnb': float(position.profit_loss_bnb) if position.profit_loss_bnb else 0,
                    'is_monitoring': position.is_monitoring,
                    'partial_sales': len(position.partial_sales)
                })
            
            portfolio_profit_loss = total_current_value - total_invested
            portfolio_profit_percent = float((portfolio_profit_loss / total_invested) * 100) if total_invested > 0 else 0
            
            summary = {
                'total_positions': len(self.positions),
                'active_positions': active_positions,
                'completed_positions': completed_positions,
                'total_invested_bnb': float(total_invested),
                'total_current_value_bnb': float(total_current_value),
                'total_profit_loss_bnb': float(portfolio_profit_loss),
                'total_profit_loss_percent': portfolio_profit_percent,
                'positions': position_summaries,
                'last_updated': int(time.time())
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating portfolio summary: {str(e)}")
            return {'error': str(e)}
    
    async def remove_position(self, token_address: str) -> bool:
        """Remove a position from portfolio"""
        try:
            if token_address in self.positions:
                del self.positions[token_address]
                self._save_portfolio()
                self.logger.info(f"Removed position: {token_address}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removing position: {str(e)}")
            return False
    
    async def start_monitoring(self):
        """Start continuous portfolio monitoring"""
        self.logger.info("Starting portfolio monitoring...")
        
        while True:
            try:
                await self.update_prices()
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in portfolio monitoring: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error

# Example usage and testing
async def test_portfolio_manager():
    """Test function for portfolio manager"""
    from trading_engine import TradingEngine
    
    trading_engine = TradingEngine()
    portfolio = PortfolioManager(trading_engine)
    
    # Get portfolio summary
    summary = await portfolio.get_portfolio_summary()
    print(f"Portfolio Summary: {summary}")

if __name__ == "__main__":
    asyncio.run(test_portfolio_manager())