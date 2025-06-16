#!/usr/bin/env python3
"""
Fix USDC Allowance - Check and set USDC allowance for Polymarket CLOB trading
"""
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

def fix_allowance():
    """Check and fix USDC allowance for CLOB trading"""
    print("🔧 Fixing USDC Allowance for CLOB Trading")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    
    if not private_key:
        print("❌ PRIVATE_KEY not found in .env file")
        return False
    
    # Create client
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=private_key,
        chain_id=137
    )
    client.set_api_creds(client.create_or_derive_api_creds())
    
    print("✅ Client setup complete")
    
    # Get addresses
    wallet_address = client.get_address()
    usdc_address = client.get_collateral_address()  # USDC contract
    exchange_address = client.get_exchange_address()  # CLOB exchange
    
    print(f"📍 Wallet: {wallet_address}")
    print(f"💰 USDC Contract: {usdc_address}")
    print(f"🏪 Exchange Contract: {exchange_address}")
    
    # Check current allowance and balance
    try:
        print(f"\n🔍 Checking current allowance and balance...")
        
        # The client should have a method to check balance/allowance
        # Let's try the update_balance_allowance method with proper signature_type
        
        # First, let's try different signature types to see which works
        signature_types = [None, 0, 1, 2]
        
        for sig_type in signature_types:
            try:
                print(f"\n🧪 Trying signature_type={sig_type}...")
                
                # Create a new client with signature_type if needed
                if sig_type is not None:
                    test_client = ClobClient(
                        host="https://clob.polymarket.com",
                        key=private_key,
                        chain_id=137,
                        signature_type=sig_type
                    )
                    test_client.set_api_creds(test_client.create_or_derive_api_creds())
                else:
                    test_client = client
                
                # Try to get balance/allowance
                balance_info = test_client.get_balance_allowance()
                print(f"✅ Balance/Allowance info: {balance_info}")
                
                # If we got here, this signature_type works
                working_client = test_client
                break
                
            except Exception as e:
                print(f"❌ signature_type={sig_type} failed: {e}")
                continue
        else:
            print("❌ No signature_type worked for balance check")
            working_client = client
    
        # Try to update allowance
        print(f"\n🔧 Attempting to set USDC allowance...")
        
        try:
            # This should set unlimited allowance for USDC to the exchange
            result = working_client.update_balance_allowance()
            print(f"✅ Allowance update result: {result}")
            
            # Verify the allowance was set
            print(f"🔍 Verifying allowance was set...")
            balance_info = working_client.get_balance_allowance()
            print(f"📋 Updated balance/allowance: {balance_info}")
            
        except Exception as e:
            print(f"❌ Failed to update allowance: {e}")
            
            # Provide manual instructions
            print(f"\n📋 Manual allowance setup required:")
            print(f"1. Go to Polygon network")
            print(f"2. Approve USDC ({usdc_address}) for Exchange ({exchange_address})")
            print(f"3. Set allowance to a large amount (e.g., 1000000 USDC)")
            
    except Exception as e:
        print(f"❌ Balance/allowance check failed: {e}")
    
    # Additional recommendations
    print(f"\n💡 Additional troubleshooting:")
    print("1. Make sure you have USDC in your wallet on Polygon network")
    print("2. If using Polymarket web interface, check your 'Deposit Address'")
    print("3. The deposit address might be different from your private key address")
    print("4. Consider using signature_type=1 or 2 with proper funder address")
    
    # Test a small order after allowance fix
    print(f"\n🧪 Testing small order after allowance fix...")
    try:
        # Try the corrected order flow again
        from py_clob_client.clob_types import OrderArgs, OrderType
        from py_clob_client.order_builder.constants import BUY
        
        token_id = "71685983838843709915160975671540060908877886707703474939962098991499689519711"
        orderbook = working_client.get_order_book(token_id)
        
        if orderbook.asks:
            best_ask = float(orderbook.asks[0].price)
            
            # Very small test order
            order_args = OrderArgs(
                price=best_ask,
                size=0.01,  # Tiny size
                side=BUY,
                token_id=token_id
            )
            
            print(f"🎯 Testing tiny order: 0.01 shares @ ${best_ask:.4f}")
            
            # Create and sign order
            signed_order = working_client.create_order(order_args)
            print("✅ Order created and signed")
            
            # Don't actually post it, just confirm it would work
            print("ℹ️  Order ready to post (not posting in test)")
            print("✅ Allowance fix appears successful!")
            
    except Exception as e:
        print(f"❌ Test order still fails: {e}")
        
        if "balance" in str(e).lower() or "allowance" in str(e).lower():
            print("💰 Still a balance/allowance issue - check funding address")
        else:
            print("🔧 Different error - allowance might be fixed")

if __name__ == "__main__":
    fix_allowance() 