#!/usr/bin/env python3
"""
Test With Funding Address - Test the updated .env configuration
"""
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY

def test_with_funding_address():
    """Test the updated .env configuration with funding address"""
    print("🧪 Testing Updated .env Configuration")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    funding_address = os.getenv("FUNDING_ADDRESS")
    
    if not private_key:
        print("❌ PRIVATE_KEY not found in .env file")
        return False
    
    print(f"✅ Private key loaded: {private_key[:10]}...")
    print(f"📍 Funding address: {funding_address or 'None'}")
    
    if not funding_address:
        print("❌ FUNDING_ADDRESS not set in .env file")
        print("💡 Make sure you added: FUNDING_ADDRESS=0xYourDepositAddress")
        return False
    
    # Get wallet address from private key
    from eth_account import Account
    account = Account.from_key(private_key)
    wallet_address = account.address
    
    print(f"🔑 Private key address: {wallet_address}")
    print(f"💰 Funding address: {funding_address}")
    
    if wallet_address.lower() == funding_address.lower():
        print("⚠️  Warning: Funding address same as private key address")
        print("   This might still be Direct EOA mode")
    else:
        print("✅ Different addresses - this looks like proxy mode")
    
    # Test different configurations
    configs = [
        {
            "name": "Direct EOA (no proxy)",
            "params": {
                "host": "https://clob.polymarket.com",
                "key": private_key,
                "chain_id": 137
            }
        },
        {
            "name": "Email/Magic proxy (signature_type=1)",
            "params": {
                "host": "https://clob.polymarket.com",
                "key": private_key,
                "chain_id": 137,
                "signature_type": 1,
                "funder": funding_address
            }
        },
        {
            "name": "Browser wallet proxy (signature_type=2)",
            "params": {
                "host": "https://clob.polymarket.com",
                "key": private_key,
                "chain_id": 137,
                "signature_type": 2,
                "funder": funding_address
            }
        }
    ]
    
    working_config = None
    
    for config in configs:
        print(f"\n🧪 Testing: {config['name']}")
        print("-" * 40)
        
        try:
            # Create client
            client = ClobClient(**config['params'])
            client.set_api_creds(client.create_or_derive_api_creds())
            print("✅ Client created and credentials set")
            
            # Test orderbook (read operation)
            token_id = "71685983838843709915160975671540060908877886707703474939962098991499689519711"
            orderbook = client.get_order_book(token_id)
            print("✅ Orderbook fetch successful")
            
            if not orderbook.asks:
                print("❌ No asks available")
                continue
                
            best_ask = float(orderbook.asks[0].price)
            print(f"💰 Best ask: ${best_ask:.4f}")
            
            # Test order creation
            order_args = OrderArgs(
                price=best_ask,
                size=0.1,  # Small but valid size
                side=BUY,
                token_id=token_id
            )
            
            signed_order = client.create_order(order_args)
            print("✅ Order created and signed successfully")
            
            # Ask if user wants to test posting
            cost = best_ask * 0.1
            confirm = input(f"🤔 Test posting ${cost:.4f} USDC order with this config? (y/n): ").lower().strip()
            
            if confirm == 'y':
                print("📤 Posting order...")
                response = client.post_order(signed_order, OrderType.GTC)
                
                print(f"📋 Response: {response}")
                
                if isinstance(response, dict):
                    success = response.get('success', False)
                    if success:
                        order_id = response.get('orderId', 'Unknown')
                        print(f"🎉 SUCCESS! Order executed with {config['name']}")
                        print(f"📋 Order ID: {order_id}")
                        working_config = config
                        break
                    else:
                        error_msg = response.get('errorMsg', 'Unknown error')
                        print(f"❌ Order failed: {error_msg}")
                        
                        # Analyze error
                        if "balance" in error_msg.lower() or "allowance" in error_msg.lower():
                            print("   💰 Still balance/allowance issue with this config")
                        else:
                            print(f"   🔧 Different error: {error_msg}")
                else:
                    print(f"⚠️  Unexpected response format: {response}")
            else:
                print("⏭️  Skipping order posting for this config")
                
        except Exception as e:
            print(f"❌ Configuration failed: {e}")
            
            # Analyze error
            error_str = str(e).lower()
            if "balance" in error_str or "allowance" in error_str:
                print("   💰 Balance/allowance issue")
            elif "signature" in error_str:
                print("   🔐 Signature issue")
            elif "403" in error_str:
                print("   🛡️  Access denied")
            else:
                print(f"   🔧 Other error")
    
    if working_config:
        print(f"\n🎉 SUCCESS! Working configuration found:")
        print(f"📋 {working_config['name']}")
        print(f"🚀 Your bot should now work with this setup!")
        
        # Update the bot's setup function
        print(f"\n💡 The bot will automatically use this configuration")
        return True
    else:
        print(f"\n❌ No configuration worked")
        print(f"🔧 Troubleshooting steps:")
        print("1. Double-check the FUNDING_ADDRESS in your .env file")
        print("2. Make sure it's the exact deposit address from Polymarket")
        print("3. Verify you have USDC balance in that address")
        print("4. Check if you need to set USDC allowance")
        return False

if __name__ == "__main__":
    success = test_with_funding_address()
    if not success:
        print("\n🔍 Debug info:")
        print("- Check your Polymarket web interface again")
        print("- Look for 'Wallet', 'Deposit', or 'Portfolio' section")
        print("- Copy the exact address where your USDC balance shows") 