import asyncio
import logging
import time
from typing import Dict, Any, Optional, Set, Callable
from web3 import Web3
from web3.contract import Contract
from web3.middleware import geth_poa_middleware
import json
import requests
import aiohttp
from config import Config
from security_analyzer import SecurityAnalyzer
import websockets
import threading
from collections import deque

class BlockchainMonitor:
    """Monitor BSC blockchain for new token launches and liquidity additions"""
    
    def __init__(self, on_new_token_callback: Optional[Callable] = None):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.web3 = Web3(Web3.HTTPProvider(self.config.BSC_RPC_URL))
        # Add POA middleware for BSC compatibility
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.on_new_token_callback = on_new_token_callback
        
        # Tracking sets
        self.monitored_tokens: Set[str] = set()
        self.processed_transactions: Set[str] = set()
        self.recent_blocks = deque(maxlen=100)  # Keep track of recent blocks
        
        # PancakeSwap contract addresses and ABIs
        self.pancakeswap_factory_address = self.config.PANCAKESWAP_FACTORY
        self.pancakeswap_router_address = self.config.PANCAKESWAP_ROUTER
        self.wbnb_address = self.config.WBNB_ADDRESS
        
        # Load contract ABIs
        self.factory_abi = self._get_pancakeswap_factory_abi()
        self.router_abi = self._get_pancakeswap_router_abi()
        self.erc20_abi = self._get_erc20_abi()
        
        # Initialize contracts
        self.factory_contract = self.web3.eth.contract(
            address=self.pancakeswap_factory_address,
            abi=self.factory_abi
        )
        self.router_contract = self.web3.eth.contract(
            address=self.pancakeswap_router_address,
            abi=self.router_abi
        )
        
        # Monitoring flags
        self.is_monitoring = False
        self.monitor_thread = None
        
    async def start_monitoring(self):
        """Start monitoring blockchain for new tokens"""
        if self.is_monitoring:
            self.logger.warning("Monitoring already started")
            return
            
        self.logger.info("Starting blockchain monitoring for new token launches...")
        self.is_monitoring = True
        
        try:
            # Verify connection
            if not self.web3.is_connected():
                raise Exception("Unable to connect to BSC network")
                
            self.logger.info(f"Connected to BSC network. Latest block: {self.web3.eth.block_number}")
            
            # Start monitoring in separate thread
            self.monitor_thread = threading.Thread(target=self._monitor_blockchain, daemon=True)
            self.monitor_thread.start()
            
            # Also start websocket monitoring for real-time updates
            await self._start_websocket_monitoring()
            
        except Exception as e:
            self.logger.error(f"Error starting blockchain monitoring: {str(e)}")
            self.is_monitoring = False
            raise
    
    def stop_monitoring(self):
        """Stop monitoring blockchain"""
        self.logger.info("Stopping blockchain monitoring...")
        self.is_monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
    
    def _monitor_blockchain(self):
        """Main monitoring loop running in separate thread"""
        latest_block = self.web3.eth.block_number
        
        while self.is_monitoring:
            try:
                current_block = self.web3.eth.block_number
                
                # Process new blocks
                if current_block > latest_block:
                    for block_num in range(latest_block + 1, current_block + 1):
                        if not self.is_monitoring:
                            break
                            
                        asyncio.run(self._process_block(block_num))
                        self.recent_blocks.append(block_num)
                    
                    latest_block = current_block
                
                time.sleep(1)  # Check for new blocks every second
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    async def _process_block(self, block_number: int):
        """Process a specific block for relevant transactions"""
        try:
            block = self.web3.eth.get_block(block_number, full_transactions=True)
            
            self.logger.debug(f"Processing block {block_number} with {len(block.transactions)} transactions")
            
            for tx in block.transactions:
                if not self.is_monitoring:
                    break
                    
                # Skip if we've already processed this transaction
                if tx.hash.hex() in self.processed_transactions:
                    continue
                    
                await self._analyze_transaction(tx, block)
                self.processed_transactions.add(tx.hash.hex())
                
                # Clean up old processed transactions to prevent memory bloat
                if len(self.processed_transactions) > 10000:
                    # Remove oldest 1000 entries
                    old_txs = list(self.processed_transactions)[:1000]
                    for old_tx in old_txs:
                        self.processed_transactions.discard(old_tx)
                        
        except Exception as e:
            self.logger.error(f"Error processing block {block_number}: {str(e)}")
    
    async def _analyze_transaction(self, tx: Dict[str, Any], block: Dict[str, Any]):
        """Analyze transaction for new token creation or liquidity addition"""
        try:
            # Check if transaction is to PancakeSwap factory (token creation)
            if tx.to and tx.to.lower() == self.pancakeswap_factory_address.lower():
                await self._handle_factory_transaction(tx, block)
            
            # Check if transaction is to PancakeSwap router (potential liquidity addition)
            elif tx.to and tx.to.lower() == self.pancakeswap_router_address.lower():
                await self._handle_router_transaction(tx, block)
                
        except Exception as e:
            self.logger.debug(f"Error analyzing transaction {tx.hash.hex()}: {str(e)}")
    
    async def _handle_factory_transaction(self, tx: Dict[str, Any], block: Dict[str, Any]):
        """Handle transactions to PancakeSwap factory (new pair creation)"""
        try:
            # Get transaction receipt for logs
            receipt = self.web3.eth.get_transaction_receipt(tx.hash)
            
            # Decode PairCreated events
            for log in receipt.logs:
                try:
                    if log.address.lower() == self.pancakeswap_factory_address.lower():
                        # Try to decode PairCreated event
                        decoded_log = self.factory_contract.events.PairCreated().processLog(log)
                        
                        token0 = decoded_log.args.token0
                        token1 = decoded_log.args.token1
                        pair_address = decoded_log.args.pair
                        
                        # Determine which token is the new token (not WBNB)
                        new_token_address = None
                        if token0.lower() != self.wbnb_address.lower():
                            new_token_address = token0
                        elif token1.lower() != self.wbnb_address.lower():
                            new_token_address = token1
                        
                        if new_token_address:
                            self.logger.info(f"New token pair created: {new_token_address}")
                            await self._handle_new_token_discovery(
                                new_token_address, 
                                pair_address, 
                                tx, 
                                block,
                                'pair_creation'
                            )
                            
                except Exception as e:
                    self.logger.debug(f"Error decoding factory log: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error handling factory transaction: {str(e)}")
    
    async def _handle_router_transaction(self, tx: Dict[str, Any], block: Dict[str, Any]):
        """Handle transactions to PancakeSwap router (liquidity additions)"""
        try:
            # Get transaction receipt for logs
            receipt = self.web3.eth.get_transaction_receipt(tx.hash)
            
            # Look for liquidity addition events
            for log in receipt.logs:
                try:
                    # Check if this is a Mint event (liquidity addition)
                    if len(log.topics) > 0 and log.topics[0].hex() == '0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f':  # Mint event signature
                        # This is a liquidity addition - get pair address
                        pair_address = log.address
                        
                        # Get pair info to determine tokens
                        token_info = await self._get_pair_token_info(pair_address)
                        if token_info:
                            token0, token1 = token_info['token0'], token_info['token1']
                            
                            # Determine which token is new (not WBNB)
                            new_token_address = None
                            if token0.lower() != self.wbnb_address.lower():
                                new_token_address = token0
                            elif token1.lower() != self.wbnb_address.lower():
                                new_token_address = token1
                            
                            if new_token_address and new_token_address not in self.monitored_tokens:
                                self.logger.info(f"Liquidity added for new token: {new_token_address}")
                                await self._handle_new_token_discovery(
                                    new_token_address,
                                    pair_address,
                                    tx,
                                    block,
                                    'liquidity_addition'
                                )
                                
                except Exception as e:
                    self.logger.debug(f"Error analyzing router log: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error handling router transaction: {str(e)}")
    
    async def _handle_new_token_discovery(
        self, 
        token_address: str, 
        pair_address: str, 
        tx: Dict[str, Any], 
        block: Dict[str, Any],
        discovery_type: str
    ):
        """Handle discovery of a new token with age filtering"""
        try:
            # Avoid duplicate processing
            if token_address in self.monitored_tokens:
                return
                
            self.logger.info(f"🔍 Checking token age for: {token_address}")
            
            # Check token age using BSC API
            token_age_minutes = await self._get_token_age_minutes(token_address)
            if token_age_minutes is None:
                self.logger.warning(f"Unable to determine token age for {token_address}")
                return
                
            # Only process fresh tokens (max 3 minutes old)
            if token_age_minutes > self.config.MAX_TOKEN_AGE_MINUTES:
                self.logger.info(f"🕐 Token too old ({token_age_minutes:.1f} min), skipping: {token_address}")
                return
                
            self.monitored_tokens.add(token_address)
            
            self.logger.info(f"🚀 FRESH TOKEN FOUND ({token_age_minutes:.1f} min old) via {discovery_type}: {token_address}")
            
            # Get basic token information
            token_info = await self._get_token_info(token_address)
            if not token_info:
                self.logger.warning(f"Unable to get token info for {token_address}")
                return
            
            # Prepare discovery data with age info
            discovery_data = {
                'token_address': token_address,
                'pair_address': pair_address,
                'discovery_type': discovery_type,
                'transaction_hash': tx.hash.hex(),
                'block_number': block.number,
                'timestamp': block.timestamp,
                'token_info': token_info,
                'token_age_minutes': token_age_minutes,
                'is_fresh': True,
                'gas_used': tx.gas,
                'gas_price': tx.gasPrice
            }
            
            # Call the callback if provided
            if self.on_new_token_callback:
                try:
                    await self.on_new_token_callback(discovery_data)
                except Exception as e:
                    self.logger.error(f"Error in new token callback: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error handling new token discovery: {str(e)}")
    
    async def _get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get basic information about a token"""
        try:
            # Create token contract instance
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.erc20_abi
            )
            
            # Get token details with error handling
            info = {'address': token_address}
            
            try:
                info['name'] = token_contract.functions.name().call()
            except:
                info['name'] = 'Unknown'
                
            try:
                info['symbol'] = token_contract.functions.symbol().call()
            except:
                info['symbol'] = 'UNKNOWN'
                
            try:
                info['decimals'] = token_contract.functions.decimals().call()
            except:
                info['decimals'] = 18
                
            try:
                info['total_supply'] = token_contract.functions.totalSupply().call()
            except:
                info['total_supply'] = 0
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting token info for {token_address}: {str(e)}")
            return None
    
    async def _get_token_age_minutes(self, token_address: str) -> Optional[float]:
        """Get token age in minutes using BSC API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get token creation transaction from BSC API
                url = "https://api.bscscan.com/api"
                params = {
                    'module': 'account',
                    'action': 'txlist',
                    'address': token_address,
                    'startblock': 0,
                    'endblock': 99999999,
                    'page': 1,
                    'offset': 1,
                    'sort': 'asc',
                    'apikey': self.config.BSC_SCAN_API_KEY
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == '1' and data.get('result'):
                            first_tx = data['result'][0]
                            creation_timestamp = int(first_tx['timeStamp'])
                            current_timestamp = int(time.time())
                            age_seconds = current_timestamp - creation_timestamp
                            age_minutes = age_seconds / 60.0
                            
                            self.logger.info(f"Token {token_address} age: {age_minutes:.1f} minutes")
                            return age_minutes
                        else:
                            # No transaction data might mean VERY fresh token!
                            self.logger.info(f"No TX data for {token_address} - likely VERY fresh token!")
                            return 0.1  # Assume super fresh (6 seconds old)
                    else:
                        self.logger.warning(f"BSC API error {response.status} - assuming fresh")
                        return 0.5  # Assume fresh if API fails
                        
        except Exception as e:
            self.logger.warning(f"BSC API timeout - assuming fresh token")
            return 0.5  # If API fails, assume it's fresh
    
    async def _get_pair_token_info(self, pair_address: str) -> Optional[Dict[str, str]]:
        """Get token addresses from a pair contract"""
        try:
            # Simplified pair ABI for token0() and token1() functions
            pair_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "token0",
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "token1", 
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function"
                }
            ]
            
            pair_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(pair_address),
                abi=pair_abi
            )
            
            token0 = pair_contract.functions.token0().call()
            token1 = pair_contract.functions.token1().call()
            
            return {'token0': token0, 'token1': token1}
            
        except Exception as e:
            self.logger.error(f"Error getting pair token info: {str(e)}")
            return None
    
    async def _start_websocket_monitoring(self):
        """Start WebSocket monitoring for real-time updates"""
        # This would typically connect to a WebSocket endpoint for real-time updates
        # For now, we'll rely on the polling method above
        # Implementation would depend on the specific WSS endpoint available
        pass
    
    def _get_pancakeswap_factory_abi(self) -> list:
        """Get PancakeSwap factory ABI"""
        return [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "token0", "type": "address"},
                    {"indexed": True, "name": "token1", "type": "address"},
                    {"indexed": False, "name": "pair", "type": "address"},
                    {"indexed": False, "name": "", "type": "uint256"}
                ],
                "name": "PairCreated",
                "type": "event"
            }
        ]
    
    def _get_pancakeswap_router_abi(self) -> list:
        """Get PancakeSwap router ABI (simplified)"""
        return [
            {
                "constant": False,
                "inputs": [
                    {"name": "tokenA", "type": "address"},
                    {"name": "tokenB", "type": "address"},
                    {"name": "amountADesired", "type": "uint256"},
                    {"name": "amountBDesired", "type": "uint256"},
                    {"name": "amountAMin", "type": "uint256"},
                    {"name": "amountBMin", "type": "uint256"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "name": "addLiquidity",
                "outputs": [
                    {"name": "amountA", "type": "uint256"},
                    {"name": "amountB", "type": "uint256"},
                    {"name": "liquidity", "type": "uint256"}
                ],
                "type": "function"
            }
        ]
    
    def _get_erc20_abi(self) -> list:
        """Get standard ERC20 ABI"""
        return [
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
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

# Example usage and testing
async def test_blockchain_monitor():
    """Test function for blockchain monitor"""
    async def on_new_token(discovery_data):
        print(f"🚀 New token discovered: {discovery_data}")
    
    monitor = BlockchainMonitor(on_new_token_callback=on_new_token)
    
    try:
        await monitor.start_monitoring()
        # Keep monitoring for 60 seconds
        await asyncio.sleep(60)
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(test_blockchain_monitor())