#!/usr/bin/env python3
"""
Polymarket Balance Checker - Check your Polymarket account balance

This script checks your balance within the Polymarket system,
which is separate from your raw wallet balance.
"""
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowbot.bot import setup_clob_client

def check_polymarket_balance():
    """Check Polymarket account balance"""
    print("💰 Checking Polymarket Account Balance")
    print("=" * 45)
    
    try:
        # Load environment
        load_dotenv()
        
        # Setup CLOB client
        print("🔗 Connecting to Polymarket CLOB...")
        client = setup_clob_client()
        print("✅ Connected successfully")
        
        # Get wallet address for reference
        private_key = os.getenv('PRIVATE_KEY')
        if private_key:
            from web3 import Web3
            account = Web3().eth.account.from_key(private_key)
            wallet_address = account.address
            print(f"🏦 Wallet Address: {wallet_address}")
        
        print("\n💵 Checking account balances...")
        
        # Try to get balance using different methods
        try:
            # Method 1: Try to get balance directly
            balance_response = client.get_balance()
            print(f"📊 Balance Response: {balance_response}")
            
            if hasattr(balance_response, 'balance'):
                balance = float(balance_response.balance)
                print(f"💰 Account Balance: ${balance:.6f} USDC")
            elif isinstance(balance_response, dict):
                if 'balance' in balance_response:
                    balance = float(balance_response['balance'])
                    print(f"💰 Account Balance: ${balance:.6f} USDC")
                else:
                    print(f"📋 Balance data: {balance_response}")
            else:
                print(f"📋 Raw balance response: {balance_response}")
                
        except Exception as e:
            print(f"❌ Error getting balance: {e}")
            print("💡 This might be normal - some balance methods require specific permissions")
        
        # Method 2: Try to get orders (which might show available balance)
        try:
            print("\n📋 Checking open orders...")
            orders = client.get_orders()
            print(f"📊 Open orders: {len(orders) if orders else 0}")
            
            if orders:
                print("🔍 Recent orders:")
                for i, order in enumerate(orders[:3]):  # Show first 3 orders
                    print(f"   {i+1}. Order ID: {getattr(order, 'id', 'Unknown')}")
                    print(f"      Status: {getattr(order, 'status', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error getting orders: {e}")
        
        # Method 3: Try to get positions
        try:
            print("\n📈 Checking positions...")
            # Note: This method might not exist in all client versions
            if hasattr(client, 'get_positions'):
                positions = client.get_positions()
                print(f"📊 Positions: {positions}")
            else:
                print("ℹ️  get_positions method not available")
                
        except Exception as e:
            print(f"❌ Error getting positions: {e}")
        
        print(f"\n💡 Note: Polymarket uses an internal balance system")
        print(f"   Your USDC is deposited into your Polymarket account")
        print(f"   This is separate from your raw wallet balance")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking Polymarket balance: {e}")
        return False

def main():
    """Main function"""
    print("🏪 Polymarket Balance Checker")
    print("Checking your internal Polymarket account balance\n")
    
    success = check_polymarket_balance()
    
    if success:
        print(f"\n✅ Connection successful!")
        print(f"💡 If you have ~$10 in your Polymarket account, you should be ready to trade")
        print(f"   The 'insufficient balance' error might be due to:")
        print(f"   1. Minimum order size requirements")
        print(f"   2. Gas fees needing to be paid in MATIC")
        print(f"   3. Order size being too large for available balance")
    else:
        print(f"\n❌ Could not check balance")
        print(f"💡 But if you can see $10 in the Polymarket UI, it should work for trading")

if __name__ == "__main__":
    main() 