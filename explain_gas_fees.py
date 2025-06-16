#!/usr/bin/env python3
"""
Gas Fee Explanation - Why you need MATIC even with Polymarket balance

This script demonstrates the blockchain transaction flow and gas requirements.
"""
import os
import sys
from dotenv import load_dotenv
from web3 import Web3

def explain_transaction_flow():
    """Explain how Polymarket transactions work"""
    print("🏗️  How Polymarket Trading Actually Works")
    print("=" * 50)
    
    print("📋 Transaction Flow:")
    print("   1. You have USDC in Polymarket account ✅")
    print("   2. You want to place a trade")
    print("   3. Polymarket creates a blockchain transaction")
    print("   4. Transaction needs gas fees (paid in MATIC) ❌")
    print("   5. No MATIC = Transaction fails immediately")
    print("   6. Trade never gets processed")
    
    print("\n💡 Key Point:")
    print("   Your Polymarket USDC balance is irrelevant if the")
    print("   transaction can't be submitted due to no gas fees!")

def estimate_gas_costs():
    """Estimate gas costs for Polymarket transactions"""
    print("\n⛽ Gas Fee Estimates")
    print("=" * 25)
    
    try:
        # Connect to Polygon
        w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
        
        # Get current gas price
        gas_price_wei = w3.eth.gas_price
        gas_price_gwei = gas_price_wei / 10**9
        
        print(f"🔥 Current Gas Price: {gas_price_gwei:.2f} Gwei")
        
        # Estimate gas for different operations
        operations = {
            "Simple Transfer": 21000,
            "Token Approval": 50000,
            "Polymarket Trade": 150000,  # Estimated
            "Complex Trade": 300000,
        }
        
        print(f"\n💰 Estimated Costs (in MATIC):")
        
        for operation, gas_limit in operations.items():
            cost_wei = gas_price_wei * gas_limit
            cost_matic = cost_wei / 10**18
            cost_usd = cost_matic * 0.50  # Rough MATIC price
            
            print(f"   {operation:20}: {cost_matic:.6f} MATIC (~${cost_usd:.4f})")
        
        print(f"\n📊 Summary:")
        print(f"   You need roughly $0.01-0.10 worth of MATIC per trade")
        print(f"   Recommended: Get $0.50-1.00 MATIC for multiple trades")
        
    except Exception as e:
        print(f"❌ Error getting gas estimates: {e}")
        print("💡 Typical costs: $0.01-0.10 per transaction")

def check_what_you_have():
    """Show current balances"""
    print("\n💰 Your Current Situation")
    print("=" * 30)
    
    try:
        load_dotenv()
        private_key = os.getenv('PRIVATE_KEY')
        
        if not private_key:
            print("❌ No private key found")
            return
        
        w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
        account = w3.eth.account.from_key(private_key)
        
        # Check MATIC
        matic_balance_wei = w3.eth.get_balance(account.address)
        matic_balance = matic_balance_wei / 10**18
        
        print(f"🏦 Wallet: {account.address}")
        print(f"🟣 MATIC Balance: {matic_balance:.6f} MATIC")
        print(f"💵 Polymarket USDC: ~$10.00 (as you mentioned)")
        
        print(f"\n🔍 Analysis:")
        if matic_balance < 0.001:
            print(f"   ❌ Insufficient MATIC for gas fees")
            print(f"   💡 Need: ~$0.50 worth of MATIC")
            print(f"   📍 Have: ${matic_balance * 0.50:.4f} worth of MATIC")
        else:
            print(f"   ✅ Sufficient MATIC for trading")
        
        print(f"   ✅ Sufficient USDC in Polymarket account")
        
    except Exception as e:
        print(f"❌ Error checking balances: {e}")

def show_solutions():
    """Show how to get MATIC"""
    print("\n🛠️  How to Get MATIC")
    print("=" * 25)
    
    print("🎯 Easiest Options:")
    print("   1. Polygon Gas Station:")
    print("      → https://wallet.polygon.technology/polygon/gas-swap")
    print("      → Swap ETH/USDC for MATIC directly")
    print("")
    print("   2. Centralized Exchange:")
    print("      → Buy MATIC on Binance/Coinbase/etc")
    print("      → Withdraw to Polygon network")
    print("      → Send to: 0x5A1256113b1592a2a4D84Fe9C9Cb608dDDB9c0f3")
    print("")
    print("   3. Bridge from Ethereum:")
    print("      → If you have ETH on mainnet")
    print("      → Bridge to Polygon and swap")
    
    print(f"\n💡 Amount Needed:")
    print(f"   Minimum: $0.50 worth of MATIC")
    print(f"   Recommended: $1-2 worth for multiple trades")

def main():
    """Main explanation"""
    print("🤔 Why Can't I Trade With Polymarket Balance?")
    print("=" * 55)
    
    explain_transaction_flow()
    estimate_gas_costs()
    check_what_you_have()
    show_solutions()
    
    print(f"\n🎯 Bottom Line:")
    print(f"   Your $10 Polymarket balance is ready to use!")
    print(f"   You just need ~$0.50 MATIC to pay blockchain gas fees")
    print(f"   Once you have MATIC → Trading will work immediately")

if __name__ == "__main__":
    main() 