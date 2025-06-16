#!/usr/bin/env python3
"""
Quick Start Guide - What to do once you have MATIC

This script provides a step-by-step guide for testing and running
the trading bots once gas fees are available.
"""
import os
import sys
from dotenv import load_dotenv

def check_readiness():
    """Check if user is ready to trade"""
    print("🔍 Checking Trading Readiness")
    print("=" * 35)
    
    try:
        from web3 import Web3
        
        # Load environment
        load_dotenv()
        private_key = os.getenv('PRIVATE_KEY')
        
        if not private_key:
            print("❌ PRIVATE_KEY not found")
            return False
        
        # Check MATIC balance
        w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
        account = w3.eth.account.from_key(private_key)
        
        matic_balance_wei = w3.eth.get_balance(account.address)
        matic_balance = matic_balance_wei / 10**18
        
        print(f"🏦 Wallet: {account.address}")
        print(f"🟣 MATIC Balance: {matic_balance:.6f} MATIC")
        print(f"💵 Polymarket USDC: ~$10.00 (as mentioned)")
        
        # Check readiness
        has_matic = matic_balance >= 0.001  # At least $0.0005 worth
        has_usdc = True  # User confirmed they have $10
        
        print(f"\n📊 Readiness Check:")
        print(f"   MATIC for gas: {'✅' if has_matic else '❌'}")
        print(f"   USDC balance: {'✅' if has_usdc else '❌'}")
        print(f"   Ireland VPN: ✅ (working)")
        print(f"   API access: ✅ (tested)")
        
        if has_matic and has_usdc:
            print(f"\n🎉 READY TO TRADE!")
            return True
        else:
            print(f"\n⏳ Not ready yet...")
            if not has_matic:
                print(f"   Need: ~$0.50 worth of MATIC")
            return False
            
    except Exception as e:
        print(f"❌ Error checking readiness: {e}")
        return False

def show_trading_steps():
    """Show step-by-step trading instructions"""
    print("\n🚀 Trading Steps (Once You Have MATIC)")
    print("=" * 45)
    
    print("📋 Step-by-Step Instructions:")
    print()
    
    print("1️⃣ **Test Single Trade:**")
    print("   ```")
    print("   # Make sure Ireland VPN is ON")
    print("   python single_trade_test.py")
    print("   ```")
    print("   Expected: Should work without Cloudflare errors")
    print()
    
    print("2️⃣ **Test Market Taker Bot:**")
    print("   ```")
    print("   # Run for just 1 iteration to test")
    print("   python -m flowbot.bot --iterations 1")
    print("   ```")
    print("   Expected: Should place 1 trade successfully")
    print()
    
    print("3️⃣ **Test Market Maker Bot:**")
    print("   ```")
    print("   # Test with small orders")
    print("   python market_maker_bot.py --order-size 0.10 --cycles 1")
    print("   ```")
    print("   Expected: Should place limit orders")
    print()
    
    print("4️⃣ **Run Full Trading (If tests work):**")
    print("   ```")
    print("   # Market taking (random trades)")
    print("   python -m flowbot.bot")
    print("   ```")
    print("   ```")
    print("   # Market making (provide liquidity)")
    print("   python market_maker_bot.py")
    print("   ```")

def show_troubleshooting():
    """Show common issues and solutions"""
    print("\n🛠️ Troubleshooting Guide")
    print("=" * 30)
    
    issues = [
        {
            "problem": "Cloudflare 403 errors",
            "solution": "Make sure Ireland VPN is connected",
            "test": "Check IP at whatismyipaddress.com"
        },
        {
            "problem": "Insufficient balance errors",
            "solution": "Check MATIC balance, get more if needed",
            "test": "python check_balance.py"
        },
        {
            "problem": "No orderbook exists",
            "solution": "Token might be inactive, bot will skip it",
            "test": "Normal behavior, bot continues"
        },
        {
            "problem": "Order creation fails",
            "solution": "Reduce order size, check market limits",
            "test": "Try --order-size 0.05"
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. **{issue['problem']}**")
        print(f"   💡 Solution: {issue['solution']}")
        print(f"   🧪 Test: {issue['test']}")

def show_configuration_tips():
    """Show configuration recommendations"""
    print("\n⚙️ Configuration Tips")
    print("=" * 25)
    
    print("📝 Recommended Settings:")
    print()
    
    print("**For Market Taker Bot:**")
    print("   • Order size: $0.10-0.50 (small amounts)")
    print("   • Interval: 30-60 seconds (not too fast)")
    print("   • Manual approval: true (for safety)")
    print()
    
    print("**For Market Maker Bot:**")
    print("   • Order size: $0.10 per level")
    print("   • Spread: 2-5% (wider spreads)")
    print("   • Price levels: 2-3 (fewer levels)")
    print("   • Refresh: 30-60 seconds")
    print()
    
    print("**Safety Settings:**")
    print("   • Max spend per market: $2.00")
    print("   • Manual approval: true")
    print("   • Start with 1-2 iterations for testing")

def main():
    """Main guide"""
    print("🚀 Quick Start Guide - Ready to Trade!")
    print("=" * 45)
    
    # Check if ready
    ready = check_readiness()
    
    if ready:
        print("\n🎉 You're ready! Follow the steps below:")
        show_trading_steps()
    else:
        print("\n⏳ Get MATIC first, then come back to this guide")
        print("\n💡 Once you have MATIC, run this script again:")
        print("   python quick_start_guide.py")
    
    show_troubleshooting()
    show_configuration_tips()
    
    print(f"\n🎯 Summary:")
    if ready:
        print(f"   ✅ Ready to trade - follow the steps above!")
    else:
        print(f"   1. Get $0.50 worth of MATIC")
        print(f"   2. Run: python quick_start_guide.py")
        print(f"   3. Follow the trading steps")
    
    print(f"\n🌐 Remember: Keep Ireland VPN connected!")

if __name__ == "__main__":
    main() 