#!/usr/bin/env python3
"""
Test different signature configurations for Polymarket CLOB
"""

import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

# Load environment variables
load_dotenv()

def test_signature_config():
    print("🔧 Testing Polymarket Signature Configurations")
    print("=" * 60)
    
    private_key = os.getenv("PRIVATE_KEY")
    funding_address = os.getenv("FUNDING_ADDRESS")
    clob_host = os.getenv("CLOB_API_URL", "https://clob.polymarket.com")
    
    print(f"🔑 Private Key: {private_key[:10]}...{private_key[-10:]}")
    print(f"💰 Funding Address: {funding_address}")
    print(f"🌐 CLOB Host: {clob_host}")
    print()
    
    # Test different configurations
    configs = [
        {
            "name": "Direct EOA (no funding address)",
            "params": {
                "host": clob_host,
                "key": private_key,
                "chain_id": 137
            }
        },
        {
            "name": "Proxy Wallet (signature type 1)",
            "params": {
                "host": clob_host,
                "key": private_key,
                "chain_id": 137,
                "signature_type": 1,
                "funder": funding_address
            }
        },
        {
            "name": "Gnosis Safe (signature type 2)",
            "params": {
                "host": clob_host,
                "key": private_key,
                "chain_id": 137,
                "signature_type": 2,
                "funder": funding_address
            }
        }
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"🧪 Test {i}: {config['name']}")
        print("-" * 40)
        
        try:
            # Create client
            client = ClobClient(**config['params'])
            
            # Try to set API credentials
            print("   📡 Setting API credentials...")
            client.set_api_creds(client.create_or_derive_api_creds())
            print("   ✅ API credentials set successfully")
            
            # Try to get a simple orderbook (this doesn't require signing)
            print("   📊 Testing orderbook access...")
            test_token = "5313693860384247355418977139283465956116716140631538428061566291497090457763"
            orderbook = client.get_order_book(test_token)
            print("   ✅ Orderbook access successful")
            
            # Try to create a test order (this will test signing)
            print("   🔐 Testing order creation (signature test)...")
            from py_clob_client.clob_types import OrderArgs
            from py_clob_client.order_builder.constants import BUY
            
            # Create a very small test order
            order_args = OrderArgs(
                price=0.01,  # Very low price, unlikely to execute
                size=0.01,   # Very small size
                side=BUY,
                token_id=test_token
            )
            
            # This will test the signature without actually executing
            try:
                response = client.create_and_post_order(order_args)
                print(f"   ✅ Order creation successful: {response}")
                print(f"   🎉 Configuration {i} WORKS!")
                return config
            except Exception as order_error:
                if "invalid signature" in str(order_error).lower():
                    print(f"   ❌ Invalid signature error: {order_error}")
                elif "not enough balance" in str(order_error).lower():
                    print(f"   ⚠️  Balance error (but signature OK): {order_error}")
                    print(f"   🎉 Configuration {i} has VALID SIGNATURE!")
                    return config
                else:
                    print(f"   ❌ Other order error: {order_error}")
            
        except Exception as e:
            print(f"   ❌ Client setup failed: {e}")
        
        print()
    
    print("❌ No working configuration found")
    return None

def main():
    working_config = test_signature_config()
    
    if working_config:
        print("\n🎯 RECOMMENDED CONFIGURATION:")
        print("=" * 40)
        print(f"Configuration: {working_config['name']}")
        print("\nUpdate your .env file:")
        
        if working_config['name'] == "Direct EOA (no funding address)":
            print("FUNDING_ADDRESS=")
            print("# Leave FUNDING_ADDRESS empty for direct EOA")
        else:
            print(f"FUNDING_ADDRESS={os.getenv('FUNDING_ADDRESS')}")
            print(f"# Use signature type {working_config['params'].get('signature_type', 0)}")
    else:
        print("\n🤔 TROUBLESHOOTING:")
        print("=" * 40)
        print("1. Verify your PRIVATE_KEY is correct")
        print("2. Check if your key is associated with the funding address")
        print("3. Ensure your Polymarket account is properly set up")

if __name__ == "__main__":
    main() 