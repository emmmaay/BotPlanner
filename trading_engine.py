import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from decimal import Decimal
import time
from config import Config
from retrying import retry

class TradingEngine:
    """Handle all trading operations on PancakeSwap"""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.web3 = Web3(Web3.HTTPProvider(self.config.BSC_RPC_URL))
        
        # Account setup
        self.account = Account.from_key(self.config.PRIVATE_KEY)
        self.wallet_address = self.account.address
        
        # Contract setup
        self.router_contract = self._setup_router_contract()
        self.wbnb_contract = self._setup_wbnb_contract()
        
        # Trading parameters
        self.gas_price = self.web3.to_wei('5', 'gwei')  # 5 gwei default
        self.gas_limit = 500000  # Default gas limit
        
        self.logger.info(f"Trading engine initialized for wallet: {self.wallet_address}")
    
    def _setup_router_contract(self) -> Contract:
        """Setup PancakeSwap router contract"""
        router_abi = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactETHForTokensSupportingFeeOnTransferTokens",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForETHSupportingFeeOnTransferTokens",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        return self.web3.eth.contract(
            address=Web3.to_checksum_address(self.config.PANCAKESWAP_ROUTER),
            abi=router_abi
        )
    
    def _setup_wbnb_contract(self) -> Contract:
        """Setup WBNB contract for interactions"""
        wbnb_abi = [
            {
                "constant": False,
                "inputs": [],
                "name": "deposit",
                "outputs": [],
                "type": "function",
                "payable": True
            },
            {
                "constant": False,
                "inputs": [{"name": "wad", "type": "uint256"}],
                "name": "withdraw",
                "outputs": [],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        return self.web3.eth.contract(
            address=Web3.to_checksum_address(self.config.WBNB_ADDRESS),
            abi=wbnb_abi
        )
    
    async def check_wallet_balance(self) -> Dict[str, Any]:
        """Check current wallet balances"""
        try:
            # Get BNB balance
            bnb_balance = self.web3.eth.get_balance(self.wallet_address)
            bnb_balance_ether = self.web3.from_wei(bnb_balance, 'ether')
            
            # Get WBNB balance
            wbnb_balance = self.wbnb_contract.functions.balanceOf(self.wallet_address).call()
            wbnb_balance_ether = self.web3.from_wei(wbnb_balance, 'ether')
            
            balance_info = {
                'bnb_balance': float(bnb_balance_ether),
                'wbnb_balance': float(wbnb_balance_ether),
                'total_balance': float(bnb_balance_ether) + float(wbnb_balance_ether),
                'gas_reserve': float(self.config.GAS_RESERVE),
                'available_for_trading': max(0, float(bnb_balance_ether) - float(self.config.GAS_RESERVE))
            }
            
            self.logger.info(f"Wallet balance: {balance_info}")
            return balance_info
            
        except Exception as e:
            self.logger.error(f"Error checking wallet balance: {str(e)}")
            return {'error': str(e)}
    
    async def buy_token(
        self, 
        token_address: str, 
        amount_bnb: Optional[Decimal] = None, 
        slippage_percent: float = 12.0
    ) -> Dict[str, Any]:
        """Buy a token with BNB"""
        try:
            # Use default amount if not specified
            if amount_bnb is None:
                amount_bnb = self.config.DEFAULT_BUY_AMOUNT
            
            amount_wei = self.web3.to_wei(amount_bnb, 'ether')
            
            self.logger.info(f"🚀 Attempting to buy {amount_bnb} BNB worth of token: {token_address}")
            
            # Check if we have enough balance
            balance_info = await self.check_wallet_balance()
            if balance_info.get('available_for_trading', 0) < float(amount_bnb):
                return {
                    'success': False,
                    'error': f"Insufficient balance. Available: {balance_info.get('available_for_trading', 0)} BNB, Required: {amount_bnb} BNB",
                    'balance_info': balance_info
                }
            
            # Get expected output amount (with slippage)
            expected_amounts = await self._get_amounts_out(amount_wei, [
                self.config.WBNB_ADDRESS,
                token_address
            ])
            
            if not expected_amounts:
                return {'success': False, 'error': 'Unable to get price quote'}
            
            expected_tokens = expected_amounts[-1]
            min_tokens = int(expected_tokens * (100 - slippage_percent) / 100)
            
            # Build transaction
            deadline = int(time.time()) + 300  # 5 minutes from now
            
            transaction = self.router_contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
                min_tokens,
                [
                    Web3.to_checksum_address(self.config.WBNB_ADDRESS),
                    Web3.to_checksum_address(token_address)
                ],
                self.wallet_address,
                deadline
            ).build_transaction({
                'from': self.wallet_address,
                'value': amount_wei,
                'gas': self.gas_limit,
                'gasPrice': self.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign and send transaction
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            self.logger.info(f"🎯 Buy transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            tx_receipt = await self._wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if tx_receipt and tx_receipt.status == 1:
                # Get actual tokens received
                actual_tokens = await self._get_token_balance_change(token_address, tx_receipt)
                
                result = {
                    'success': True,
                    'transaction_hash': tx_hash.hex(),
                    'amount_bnb': float(amount_bnb),
                    'expected_tokens': expected_tokens,
                    'actual_tokens': actual_tokens,
                    'slippage_percent': slippage_percent,
                    'gas_used': tx_receipt.gasUsed,
                    'timestamp': int(time.time()),
                    'block_number': tx_receipt.blockNumber
                }
                
                self.logger.info(f"✅ Token purchase successful: {result}")
                return result
            else:
                return {
                    'success': False,
                    'error': 'Transaction failed',
                    'transaction_hash': tx_hash.hex(),
                    'receipt': tx_receipt
                }
                
        except Exception as e:
            self.logger.error(f"Error buying token: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def sell_token(
        self, 
        token_address: str, 
        amount_tokens: int, 
        slippage_percent: float = 12.0
    ) -> Dict[str, Any]:
        """Sell tokens for BNB"""
        try:
            self.logger.info(f"💰 Attempting to sell {amount_tokens} tokens of {token_address}")
            
            # First approve the router to spend tokens
            approval_result = await self._approve_token(token_address, amount_tokens)
            if not approval_result['success']:
                return approval_result
            
            # Get expected BNB output
            expected_amounts = await self._get_amounts_out(amount_tokens, [
                token_address,
                self.config.WBNB_ADDRESS
            ])
            
            if not expected_amounts:
                return {'success': False, 'error': 'Unable to get price quote'}
            
            expected_bnb = expected_amounts[-1]
            min_bnb = int(expected_bnb * (100 - slippage_percent) / 100)
            
            # Build transaction
            deadline = int(time.time()) + 300  # 5 minutes from now
            
            transaction = self.router_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                amount_tokens,
                min_bnb,
                [
                    Web3.to_checksum_address(token_address),
                    Web3.to_checksum_address(self.config.WBNB_ADDRESS)
                ],
                self.wallet_address,
                deadline
            ).build_transaction({
                'from': self.wallet_address,
                'gas': self.gas_limit,
                'gasPrice': self.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign and send transaction
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            self.logger.info(f"💸 Sell transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            tx_receipt = await self._wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if tx_receipt and tx_receipt.status == 1:
                actual_bnb = self.web3.from_wei(expected_bnb, 'ether')  # Simplified - you'd track actual change
                
                result = {
                    'success': True,
                    'transaction_hash': tx_hash.hex(),
                    'amount_tokens': amount_tokens,
                    'expected_bnb': float(actual_bnb),
                    'actual_bnb': float(actual_bnb),
                    'slippage_percent': slippage_percent,
                    'gas_used': tx_receipt.gasUsed,
                    'timestamp': int(time.time()),
                    'block_number': tx_receipt.blockNumber
                }
                
                self.logger.info(f"✅ Token sale successful: {result}")
                return result
            else:
                return {
                    'success': False,
                    'error': 'Transaction failed',
                    'transaction_hash': tx_hash.hex(),
                    'receipt': tx_receipt
                }
                
        except Exception as e:
            self.logger.error(f"Error selling token: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    async def _get_amounts_out(self, amount_in: int, path: list) -> Optional[list]:
        """Get expected output amounts for a trade"""
        try:
            amounts = self.router_contract.functions.getAmountsOut(
                amount_in,
                [Web3.to_checksum_address(addr) for addr in path]
            ).call()
            return amounts
        except Exception as e:
            self.logger.error(f"Error getting amounts out: {str(e)}")
            return None
    
    async def _approve_token(self, token_address: str, amount: int) -> Dict[str, Any]:
        """Approve router to spend tokens"""
        try:
            # Standard ERC20 approve function ABI
            approve_abi = [
                {
                    "constant": False,
                    "inputs": [
                        {"name": "_spender", "type": "address"},
                        {"name": "_value", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function"
                }
            ]
            
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=approve_abi
            )
            
            # Build approval transaction
            transaction = token_contract.functions.approve(
                self.config.PANCAKESWAP_ROUTER,
                amount
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 100000,
                'gasPrice': self.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign and send
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            tx_receipt = await self._wait_for_transaction_receipt(tx_hash, timeout=30)
            
            if tx_receipt and tx_receipt.status == 1:
                return {'success': True, 'tx_hash': tx_hash.hex()}
            else:
                return {'success': False, 'error': 'Approval transaction failed'}
                
        except Exception as e:
            self.logger.error(f"Error approving token: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _wait_for_transaction_receipt(self, tx_hash, timeout: int = 60):
        """Wait for transaction confirmation"""
        try:
            for _ in range(timeout):
                try:
                    receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                    if receipt:
                        return receipt
                except:
                    pass
                await asyncio.sleep(1)
            
            self.logger.warning(f"Transaction {tx_hash.hex()} timed out after {timeout} seconds")
            return None
            
        except Exception as e:
            self.logger.error(f"Error waiting for transaction receipt: {str(e)}")
            return None
    
    async def _get_token_balance_change(self, token_address: str, tx_receipt) -> int:
        """Get actual tokens received from transaction logs"""
        try:
            # This is a simplified version - in practice you'd parse Transfer events
            # from the transaction receipt to get exact token amounts
            return 0  # Placeholder
        except Exception as e:
            self.logger.error(f"Error getting token balance change: {str(e)}")
            return 0
    
    async def get_token_price_bnb(self, token_address: str, amount_tokens: int = None) -> Optional[Decimal]:
        """Get current token price in BNB"""
        try:
            if amount_tokens is None:
                amount_tokens = 10**18  # 1 token with 18 decimals
            
            amounts = await self._get_amounts_out(amount_tokens, [
                token_address,
                self.config.WBNB_ADDRESS
            ])
            
            if amounts:
                bnb_amount = self.web3.from_wei(amounts[-1], 'ether')
                token_amount = amount_tokens / (10**18)
                return Decimal(str(bnb_amount)) / Decimal(str(token_amount))
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting token price: {str(e)}")
            return None
    
    async def estimate_gas_price(self) -> int:
        """Get optimal gas price for fast execution"""
        try:
            # Get current gas price and add premium for fast execution
            current_gas_price = self.web3.eth.gas_price
            fast_gas_price = int(current_gas_price * 1.2)  # 20% premium
            
            # Cap at reasonable maximum (50 gwei)
            max_gas_price = self.web3.to_wei('50', 'gwei')
            
            optimal_gas_price = min(fast_gas_price, max_gas_price)
            self.gas_price = optimal_gas_price
            
            return optimal_gas_price
            
        except Exception as e:
            self.logger.error(f"Error estimating gas price: {str(e)}")
            return self.gas_price

# Example usage and testing
async def test_trading_engine():
    """Test function for trading engine"""
    engine = TradingEngine()
    
    # Check balance
    balance = await engine.check_wallet_balance()
    print(f"Balance: {balance}")
    
    # Test price quote (using USDT as example)
    usdt_address = "0x55d398326f99059fF775485246999027B3197955"
    price = await engine.get_token_price_bnb(usdt_address)
    print(f"USDT price: {price} BNB")

if __name__ == "__main__":
    asyncio.run(test_trading_engine())