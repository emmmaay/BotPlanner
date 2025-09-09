import requests
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from config import Config
from retrying import retry
import time

class SecurityAnalyzer:
    """Comprehensive security analyzer using Go Plus API and custom checks"""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    async def _make_goplus_request(self, endpoint: str, params: dict) -> Dict[str, Any]:
        """Make authenticated request to Go Plus API with retry logic"""
        try:
            headers = {
                'Authorization': f'Bearer {self.config.GOPLUS_APP_KEY}',
                'X-API-SECRET': self.config.GOPLUS_APP_SECRET,
                'Content-Type': 'application/json'
            }
            
            url = f"{self.config.GOPLUS_BASE_URL}{endpoint}"
            
            async with self.session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    self.logger.error(f"Go Plus API error: {response.status} - {await response.text()}")
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Error making Go Plus request: {str(e)}")
            raise
    
    async def analyze_token_security(self, token_address: str, chain_id: str = "56") -> Dict[str, Any]:
        """Perform comprehensive security analysis on a token"""
        try:
            self.logger.info(f"Starting security analysis for token: {token_address}")
            
            # Get token security from Go Plus
            security_data = await self._get_goplus_security(token_address, chain_id)
            
            # Perform additional custom checks
            custom_checks = await self._perform_custom_checks(token_address, security_data)
            
            # Calculate overall security score
            security_score = self._calculate_security_score(security_data, custom_checks)
            
            analysis_result = {
                'token_address': token_address,
                'security_score': security_score,
                'is_safe': security_score >= 80,  # 80% threshold for safety
                'goplus_data': security_data,
                'custom_checks': custom_checks,
                'timestamp': int(time.time()),
                'detailed_analysis': self._generate_detailed_analysis(security_data, custom_checks)
            }
            
            self.logger.info(f"Security analysis completed. Score: {security_score}% - {'SAFE' if analysis_result['is_safe'] else 'UNSAFE'}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error analyzing token security: {str(e)}")
            return {
                'token_address': token_address,
                'security_score': 0,
                'is_safe': False,
                'error': str(e),
                'timestamp': int(time.time())
            }
    
    async def _get_goplus_security(self, token_address: str, chain_id: str) -> Dict[str, Any]:
        """Get security data from Go Plus API"""
        try:
            # Token security check
            params = {
                'chain_id': chain_id,
                'contract_addresses': token_address
            }
            
            security_data = await self._make_goplus_request('/api/v1/token_security/', params)
            
            if security_data and 'result' in security_data:
                token_data = security_data['result'].get(token_address.lower(), {})
                return token_data
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting Go Plus security data: {str(e)}")
            return {}
    
    async def _perform_custom_checks(self, token_address: str, goplus_data: Dict) -> Dict[str, Any]:
        """Perform additional custom security checks"""
        checks = {}
        
        try:
            # Check 1: Honeypot detection
            checks['honeypot_check'] = await self._check_honeypot(goplus_data)
            
            # Check 2: Liquidity analysis
            checks['liquidity_check'] = await self._check_liquidity(goplus_data)
            
            # Check 3: Holder distribution analysis
            checks['holder_check'] = await self._check_holder_distribution(token_address, goplus_data)
            
            # Check 4: Contract verification
            checks['contract_verification'] = await self._check_contract_verification(goplus_data)
            
            # Check 5: Trading tax analysis
            checks['tax_analysis'] = await self._analyze_trading_taxes(goplus_data)
            
            # Check 6: Mint function check
            checks['mint_check'] = await self._check_mint_function(goplus_data)
            
            # Check 7: Ownership check
            checks['ownership_check'] = await self._check_ownership(goplus_data)
            
            # Check 8: Proxy contract check
            checks['proxy_check'] = await self._check_proxy_contract(goplus_data)
            
            # Check 9: External call check
            checks['external_call_check'] = await self._check_external_calls(goplus_data)
            
            # Check 10: Hidden owner check
            checks['hidden_owner_check'] = await self._check_hidden_owner(goplus_data)
            
            return checks
            
        except Exception as e:
            self.logger.error(f"Error performing custom checks: {str(e)}")
            return {'error': str(e)}
    
    async def _check_honeypot(self, goplus_data: Dict) -> Dict[str, Any]:
        """Check if token is a honeypot"""
        try:
            is_honeypot = goplus_data.get('is_honeypot', '0') == '1'
            honeypot_with_same_creator = goplus_data.get('honeypot_with_same_creator', '0') == '1'
            
            return {
                'is_safe': not (is_honeypot or honeypot_with_same_creator),
                'is_honeypot': is_honeypot,
                'honeypot_with_same_creator': honeypot_with_same_creator,
                'score': 0 if (is_honeypot or honeypot_with_same_creator) else 100
            }
        except:
            return {'is_safe': False, 'score': 0, 'error': 'Unable to check honeypot'}
    
    async def _check_liquidity(self, goplus_data: Dict) -> Dict[str, Any]:
        """Analyze liquidity safety"""
        try:
            total_supply = float(goplus_data.get('total_supply', '0'))
            lp_total_supply = float(goplus_data.get('lp_total_supply', '0'))
            
            if total_supply == 0:
                return {'is_safe': False, 'score': 0, 'reason': 'No total supply data'}
            
            liquidity_ratio = (lp_total_supply / total_supply) * 100 if total_supply > 0 else 0
            
            # Good liquidity should be at least 50% of total supply
            is_safe = liquidity_ratio >= 50
            score = min(100, liquidity_ratio * 2)  # Scale to 100
            
            return {
                'is_safe': is_safe,
                'liquidity_ratio': liquidity_ratio,
                'score': score,
                'lp_total_supply': lp_total_supply,
                'total_supply': total_supply
            }
        except:
            return {'is_safe': False, 'score': 0, 'error': 'Unable to analyze liquidity'}
    
    async def _check_holder_distribution(self, token_address: str, goplus_data: Dict) -> Dict[str, Any]:
        """Analyze holder distribution for concentration risk"""
        try:
            # Get top 10 holders data from Go Plus
            holder_count = int(goplus_data.get('holder_count', '0'))
            
            # For new tokens at launch, holder count might be low
            # Implement smart logic here
            if holder_count <= 2:  # Likely at launch
                # Check if trading has started
                is_trading = goplus_data.get('is_trading', '0') == '1'
                if not is_trading:
                    # Token hasn't started trading yet, this might be acceptable
                    return {
                        'is_safe': True,
                        'score': 70,  # Moderate score for launch phase
                        'reason': 'Token at launch phase',
                        'holder_count': holder_count,
                        'at_launch': True
                    }
            
            # For tokens with trading activity
            if holder_count < self.config.MIN_HOLDERS_COUNT:
                return {
                    'is_safe': False,
                    'score': 20,
                    'reason': f'Too few holders: {holder_count}',
                    'holder_count': holder_count
                }
            
            # Check for whale concentration
            # This is a simplified check - in practice you'd want more detailed holder analysis
            score = min(100, (holder_count / 100) * 100)  # Scale based on holder count
            is_safe = holder_count >= self.config.MIN_HOLDERS_COUNT
            
            return {
                'is_safe': is_safe,
                'score': score,
                'holder_count': holder_count,
                'at_launch': False
            }
            
        except:
            return {'is_safe': False, 'score': 0, 'error': 'Unable to analyze holder distribution'}
    
    async def _check_contract_verification(self, goplus_data: Dict) -> Dict[str, Any]:
        """Check if contract is verified"""
        try:
            is_open_source = goplus_data.get('is_open_source', '0') == '1'
            
            return {
                'is_safe': is_open_source,
                'is_open_source': is_open_source,
                'score': 100 if is_open_source else 0
            }
        except:
            return {'is_safe': False, 'score': 0, 'error': 'Unable to check contract verification'}
    
    async def _analyze_trading_taxes(self, goplus_data: Dict) -> Dict[str, Any]:
        """Analyze buy and sell taxes"""
        try:
            buy_tax = float(goplus_data.get('buy_tax', '0'))
            sell_tax = float(goplus_data.get('sell_tax', '0'))
            
            # Reasonable tax thresholds
            max_acceptable_tax = 10.0  # 10%
            
            buy_tax_safe = buy_tax <= max_acceptable_tax
            sell_tax_safe = sell_tax <= max_acceptable_tax
            
            is_safe = buy_tax_safe and sell_tax_safe
            
            # Score based on tax levels
            buy_score = max(0, 100 - (buy_tax * 10))  # Each 1% tax reduces score by 10
            sell_score = max(0, 100 - (sell_tax * 10))
            overall_score = (buy_score + sell_score) / 2
            
            return {
                'is_safe': is_safe,
                'buy_tax': buy_tax,
                'sell_tax': sell_tax,
                'buy_tax_safe': buy_tax_safe,
                'sell_tax_safe': sell_tax_safe,
                'score': overall_score
            }
        except:
            return {'is_safe': False, 'score': 0, 'error': 'Unable to analyze trading taxes'}
    
    async def _check_mint_function(self, goplus_data: Dict) -> Dict[str, Any]:
        """Check for mint function risks"""
        try:
            can_take_back_ownership = goplus_data.get('can_take_back_ownership', '0') == '1'
            is_mintable = goplus_data.get('is_mintable', '0') == '1'
            
            is_safe = not (can_take_back_ownership or is_mintable)
            
            return {
                'is_safe': is_safe,
                'can_take_back_ownership': can_take_back_ownership,
                'is_mintable': is_mintable,
                'score': 100 if is_safe else 0
            }
        except:
            return {'is_safe': False, 'score': 0, 'error': 'Unable to check mint function'}
    
    async def _check_ownership(self, goplus_data: Dict) -> Dict[str, Any]:
        """Check ownership related risks"""
        try:
            owner_change_balance = goplus_data.get('owner_change_balance', '0') == '1'
            cannot_sell_all = goplus_data.get('cannot_sell_all', '0') == '1'
            
            is_safe = not (owner_change_balance or cannot_sell_all)
            
            return {
                'is_safe': is_safe,
                'owner_change_balance': owner_change_balance,
                'cannot_sell_all': cannot_sell_all,
                'score': 100 if is_safe else 0
            }
        except:
            return {'is_safe': False, 'score': 0, 'error': 'Unable to check ownership'}
    
    async def _check_proxy_contract(self, goplus_data: Dict) -> Dict[str, Any]:
        """Check for proxy contract risks"""
        try:
            is_proxy = goplus_data.get('is_proxy', '0') == '1'
            
            # Proxy contracts can be risky as they can be upgraded
            is_safe = not is_proxy
            
            return {
                'is_safe': is_safe,
                'is_proxy': is_proxy,
                'score': 100 if is_safe else 30  # Partial score for proxy contracts
            }
        except:
            return {'is_safe': True, 'score': 100, 'error': 'Unable to check proxy contract'}
    
    async def _check_external_calls(self, goplus_data: Dict) -> Dict[str, Any]:
        """Check for external call risks"""
        try:
            external_call = goplus_data.get('external_call', '0') == '1'
            
            # External calls can introduce risks
            is_safe = not external_call
            
            return {
                'is_safe': is_safe,
                'external_call': external_call,
                'score': 100 if is_safe else 40
            }
        except:
            return {'is_safe': True, 'score': 100, 'error': 'Unable to check external calls'}
    
    async def _check_hidden_owner(self, goplus_data: Dict) -> Dict[str, Any]:
        """Check for hidden owner risks"""
        try:
            hidden_owner = goplus_data.get('hidden_owner', '0') == '1'
            
            is_safe = not hidden_owner
            
            return {
                'is_safe': is_safe,
                'hidden_owner': hidden_owner,
                'score': 100 if is_safe else 0
            }
        except:
            return {'is_safe': True, 'score': 100, 'error': 'Unable to check hidden owner'}
    
    def _calculate_security_score(self, goplus_data: Dict, custom_checks: Dict) -> int:
        """Calculate overall security score based on all checks"""
        try:
            scores = []
            weights = []
            
            # Critical checks (higher weight)
            critical_checks = ['honeypot_check', 'hidden_owner_check', 'mint_check']
            for check_name in critical_checks:
                if check_name in custom_checks and 'score' in custom_checks[check_name]:
                    scores.append(custom_checks[check_name]['score'])
                    weights.append(3)  # Higher weight for critical checks
            
            # Important checks (medium weight)
            important_checks = ['liquidity_check', 'ownership_check', 'tax_analysis', 'contract_verification']
            for check_name in important_checks:
                if check_name in custom_checks and 'score' in custom_checks[check_name]:
                    scores.append(custom_checks[check_name]['score'])
                    weights.append(2)
            
            # Standard checks (normal weight)
            standard_checks = ['holder_check', 'proxy_check', 'external_call_check']
            for check_name in standard_checks:
                if check_name in custom_checks and 'score' in custom_checks[check_name]:
                    scores.append(custom_checks[check_name]['score'])
                    weights.append(1)
            
            if not scores:
                return 0
            
            # Calculate weighted average
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            
            overall_score = int(weighted_sum / total_weight) if total_weight > 0 else 0
            
            return max(0, min(100, overall_score))  # Ensure score is between 0-100
            
        except Exception as e:
            self.logger.error(f"Error calculating security score: {str(e)}")
            return 0
    
    def _generate_detailed_analysis(self, goplus_data: Dict, custom_checks: Dict) -> Dict[str, Any]:
        """Generate detailed analysis report"""
        try:
            analysis = {
                'summary': {},
                'risks': [],
                'strengths': [],
                'recommendations': []
            }
            
            # Analyze each check and generate insights
            for check_name, check_data in custom_checks.items():
                if isinstance(check_data, dict):
                    if check_data.get('is_safe', False):
                        analysis['strengths'].append(f"{check_name.replace('_', ' ').title()}: Passed")
                    else:
                        risk_reason = check_data.get('reason', check_data.get('error', 'Failed security check'))
                        analysis['risks'].append(f"{check_name.replace('_', ' ').title()}: {risk_reason}")
            
            # Generate recommendations based on risks
            if len(analysis['risks']) == 0:
                analysis['recommendations'].append("Token appears safe for investment")
            elif len(analysis['risks']) <= 2:
                analysis['recommendations'].append("Low risk token - proceed with caution")
            else:
                analysis['recommendations'].append("High risk token - avoid investment")
            
            return analysis
            
        except Exception as e:
            return {'error': f"Error generating detailed analysis: {str(e)}"}

# Example usage and testing
async def test_security_analyzer():
    """Test function for the security analyzer"""
    analyzer = SecurityAnalyzer()
    
    # Test with a known token address (USDT on BSC for testing)
    test_token = "0x55d398326f99059fF775485246999027B3197955"
    
    async with analyzer:
        result = await analyzer.analyze_token_security(test_token)
        print(f"Security Analysis Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_security_analyzer())