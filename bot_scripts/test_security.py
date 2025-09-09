#!/usr/bin/env python3
"""
Test script specifically for security analysis functionality
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from security_analyzer import SecurityAnalyzer

async def test_security_analysis():
    """Test the security analysis with real tokens"""
    print("🛡️ Testing Security Analysis System")
    print("=" * 50)
    
    try:
        analyzer = SecurityAnalyzer()
        
        # Test with known safe token (USDT on BSC)
        print("🧪 Testing with USDT (known safe token)...")
        usdt_address = "0x55d398326f99059fF775485246999027B3197955"
        
        async with analyzer:
            usdt_result = await analyzer.analyze_token_security(usdt_address)
        
        print(f"📊 USDT Analysis Result:")
        print(f"   Security Score: {usdt_result.get('security_score', 'N/A')}%")
        print(f"   Is Safe: {usdt_result.get('is_safe', False)}")
        print(f"   Checks Performed: {len(usdt_result.get('custom_checks', {}))}")
        
        # Show detailed checks
        if 'custom_checks' in usdt_result:
            print("\n🔍 Detailed Security Checks:")
            for check_name, check_data in usdt_result['custom_checks'].items():
                if isinstance(check_data, dict):
                    status = "✅ PASS" if check_data.get('is_safe', False) else "❌ FAIL"
                    score = check_data.get('score', 0)
                    print(f"   {check_name.replace('_', ' ').title()}: {status} (Score: {score})")
        
        # Test with another token (BUSD)
        print("\n🧪 Testing with BUSD (another known token)...")
        busd_address = "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"
        
        async with analyzer:
            busd_result = await analyzer.analyze_token_security(busd_address)
        
        print(f"📊 BUSD Analysis Result:")
        print(f"   Security Score: {busd_result.get('security_score', 'N/A')}%")
        print(f"   Is Safe: {busd_result.get('is_safe', False)}")
        
        # Test Go Plus API connection specifically
        print("\n🔗 Testing Go Plus API Connection...")
        if 'goplus_data' in usdt_result and usdt_result['goplus_data']:
            print("✅ Go Plus API connection successful")
            goplus_data = usdt_result['goplus_data']
            print(f"   Honeypot Status: {goplus_data.get('is_honeypot', 'Unknown')}")
            print(f"   Is Open Source: {goplus_data.get('is_open_source', 'Unknown')}")
            print(f"   Buy Tax: {goplus_data.get('buy_tax', 'Unknown')}%")
            print(f"   Sell Tax: {goplus_data.get('sell_tax', 'Unknown')}%")
        else:
            print("⚠️ Go Plus API returned no data - check API keys")
        
        # Test all security checks
        print("\n🔐 Security Check Coverage:")
        expected_checks = [
            'honeypot_check', 'liquidity_check', 'holder_check', 
            'contract_verification', 'tax_analysis', 'mint_check',
            'ownership_check', 'proxy_check', 'external_call_check', 
            'hidden_owner_check'
        ]
        
        performed_checks = list(usdt_result.get('custom_checks', {}).keys())
        
        for check in expected_checks:
            if check in performed_checks:
                print(f"   ✅ {check.replace('_', ' ').title()}")
            else:
                print(f"   ❌ {check.replace('_', ' ').title()} - MISSING")
        
        # Overall assessment
        print(f"\n📋 Security Analysis Summary:")
        print(f"   Total Checks Implemented: {len(performed_checks)}")
        print(f"   Expected Checks: {len(expected_checks)}")
        print(f"   Coverage: {len(performed_checks)/len(expected_checks)*100:.1f}%")
        
        if len(performed_checks) >= 8 and usdt_result.get('security_score', 0) > 0:
            print("\n🎉 Security Analysis System: FULLY OPERATIONAL!")
            print("🛡️ Your bot can detect:")
            print("   • Honeypots and rug pulls")
            print("   • Unsafe holder distribution")
            print("   • High trading taxes")
            print("   • Mint functions and ownership risks")
            print("   • Contract verification status")
            print("   • Hidden owners and proxy contracts")
            print("   • External call risks")
            print("   • Liquidity safety")
            return True
        else:
            print("\n⚠️ Security analysis needs attention")
            return False
            
    except Exception as e:
        print(f"❌ Security analysis test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_security_analysis())
    sys.exit(0 if success else 1)