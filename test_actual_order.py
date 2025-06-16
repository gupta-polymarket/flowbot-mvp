#!/usr/bin/env python3
"""
Test Actual Order - Try to post a very small order to see the real error
"""
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY

def test_actual_order():
    """Test posting a very small actual order"""
    print("🎯 Testing Actual Order Posting")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    funding_address = os.getenv("FUNDING_ADDRESS")
    
    if not private_key:
        print("❌ PRIVATE_KEY not found in .env file")
        return False
    
    print(f"✅ Private key loaded")
    print(f"📋 Funding address: {funding_address or 'None (Direct EOA)'}")
    
    # Test different client configurations
    configs = [
        {
            "name": "Direct EOA",
            "params": {
                "host": "https://clob.polymarket.com",
                "key": private_key,
                "chain_id": 137
            }
        }
    ]
    
    # Add proxy configs if we have a funding address
    if funding_address:
        configs.extend([
            {
                "name": "Email/Magic proxy",
                "params": {
                    "host": "https://clob.polymarket.com",
                    "key": private_key,
                    "chain_id": 137,
                    "signature_type": 1,
                    "funder": funding_address
                }
            },
            {
                "name": "Browser wallet proxy",
                "params": {
                    "host": "https://clob.polymarket.com",
                    "key": private_key,
                    "chain_id": 137,
                    "signature_type": 2,
                    "funder": funding_address
                }
            }
        ])
    
    for config in configs:
        print(f"\n🧪 Testing: {config['name']}")
        print("-" * 40)
        
        try:
            # Create client
            client = ClobClient(**config['params'])
            client.set_api_creds(client.create_or_derive_api_creds())
            print("✅ Client setup complete")
            
            # Get orderbook
            token_id = "71685983838843709915160975671540060908877886707703474939962098991499689519711"
            orderbook = client.get_order_book(token_id)
            
            if not orderbook.asks:
                print("❌ No asks available")
                continue
                
            best_ask = float(orderbook.asks[0].price)
            print(f"💰 Best ask: ${best_ask:.4f}")
            
            # Create a VERY small order
            order_args = OrderArgs(
                price=best_ask,
                size=0.001,  # Extremely small - about $0.001 USDC
                side=BUY,
                token_id=token_id
            )
            
            print(f"🎯 Creating tiny order: 0.001 shares @ ${best_ask:.4f} (${best_ask * 0.001:.6f} USDC)")
            
            # Create and sign order
            signed_order = client.create_order(order_args)
            print("✅ Order created and signed")
            
            # Ask for confirmation before posting
            confirm = input(f"🤔 Post this tiny ${best_ask * 0.001:.6f} USDC order? (y/n): ").lower().strip()
            if confirm != 'y':
                print("❌ Order cancelled by user")
                continue
            
            # Post the order
            print("📤 Posting order...")
            response = client.post_order(signed_order, OrderType.GTC)
            
            print(f"🎉 ORDER POSTED SUCCESSFULLY!")
            print(f"📋 Response: {response}")
            
            # Check response details
            if isinstance(response, dict):
                success = response.get('success', False)
                if success:
                    order_id = response.get('orderId', 'Unknown')
                    print(f"✅ Order executed! Order ID: {order_id}")
                    print(f"🎯 Configuration '{config['name']}' WORKS!")
                    return True
                else:
                    error_msg = response.get('errorMsg', 'Unknown error')
                    print(f"❌ Order failed: {error_msg}")
            else:
                print(f"⚠️  Unexpected response format: {response}")
                
        except Exception as e:
            print(f"❌ Configuration '{config['name']}' failed: {e}")
            
            # Analyze the error
            error_str = str(e).lower()
            if "balance" in error_str or "allowance" in error_str:
                print("   💰 Balance/allowance issue")
                if "balance" in error_str:
                    print("   💡 Try: Check USDC balance in wallet or Polymarket deposit address")
                if "allowance" in error_str:
                    print("   💡 Try: Set USDC allowance for CLOB exchange contract")
            elif "signature" in error_str:
                print("   🔐 Signature issue - wrong private key or proxy setup")
            elif "403" in error_str:
                print("   🛡️  Access denied - Cloudflare or authentication")
            else:
                print(f"   🔧 Other error: {e}")
    
    print(f"\n💡 Summary:")
    print("If all configurations failed with balance/allowance errors:")
    print("1. Your private key works for signing")
    print("2. But USDC funds are not accessible")
    print("3. Check your Polymarket web interface for the correct 'Deposit Address'")
    print("4. That deposit address should be used as FUNDING_ADDRESS in .env")
    
    return False

if __name__ == "__main__":
    success = test_actual_order()
    if success:
        print("\n✅ ACTUAL ORDER TEST PASSED - Bot should work!")
    else:
        print("\n❌ ACTUAL ORDER TEST FAILED - Need to fix funding setup") 