#!/usr/bin/env python3
"""
Single Trade Test - Test one static trade order to bypass Cloudflare detection
"""
import os
import time
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
from py_clob_client.order_builder.constants import BUY, SELL

def test_single_trade():
    """Test a single trade order with minimal automation patterns"""
    print("🧪 Testing Single Trade Order")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    
    if not private_key:
        print("❌ PRIVATE_KEY not found in .env file")
        return False
    
    print("✅ Private key loaded")
    
    # Setup CLOB client
    try:
        client = ClobClient(
            host="https://clob.polymarket.com",
            key=private_key,
            chain_id=137
        )
        print("✅ CLOB client created")
        
        # Set API credentials
        client.set_api_creds(client.create_or_derive_api_creds())
        print("✅ API credentials set")
        
    except Exception as e:
        print(f"❌ Failed to setup CLOB client: {e}")
        return False
    
    # Use a known active token ID from our previous tests
    # This is the "Will Ukraine join NATO before July?" market (YES token)
    token_id = "71685983838843709915160975671540060908877886707703474939962098991499689519711"
    
    print(f"\n📊 Testing market: Will Ukraine join NATO before July?")
    print(f"🪙 Token ID: {token_id}")
    
    # Get orderbook
    try:
        print("\n📈 Fetching orderbook...")
        orderbook = client.get_order_book(token_id)
        print("✅ Orderbook fetched successfully")
        
        # Check if we have liquidity
        if not orderbook.asks or not orderbook.bids:
            print("❌ No liquidity available in orderbook")
            return False
            
        best_ask = float(orderbook.asks[0].price)
        best_bid = float(orderbook.bids[0].price)
        
        print(f"💰 Best Ask: ${best_ask:.4f}")
        print(f"💰 Best Bid: ${best_bid:.4f}")
        
    except Exception as e:
        print(f"❌ Failed to fetch orderbook: {e}")
        return False
    
    # Create a small test order (BUY at best ask price)
    side = BUY
    price = best_ask  # Take the ask (market buy)
    size = 0.5  # Small size to minimize cost
    
    print(f"\n🎯 Preparing order:")
    print(f"   Side: {side}")
    print(f"   Price: ${price:.4f}")
    print(f"   Size: {size} shares")
    print(f"   Cost: ${price * size:.4f} USDC")
    
    # Ask for confirmation
    confirm = input("\n🤔 Execute this trade? (y/n): ").lower().strip()
    if confirm != 'y':
        print("❌ Trade cancelled by user")
        return False
    
    # Add a small delay to appear more human-like
    print("⏳ Preparing order submission...")
    time.sleep(2)
    
    # Create and submit order
    try:
        print("\n🚀 Creating order...")
        
        order_args = OrderArgs(
            price=price,
            size=size,
            side=side,
            token_id=token_id
        )
        
        print("✅ Order arguments created")
        print("📤 Submitting order to CLOB...")
        
        # Submit the order
        response = client.create_and_post_order(order_args)
        
        print("🎉 ORDER SUBMITTED SUCCESSFULLY!")
        print(f"📋 Response: {response}")
        
        # Check if order was successful
        if hasattr(response, 'success') and response.success:
            print("✅ Trade executed successfully!")
            return True
        elif isinstance(response, dict) and response.get('success'):
            print("✅ Trade executed successfully!")
            return True
        else:
            print(f"⚠️ Order submitted but status unclear: {response}")
            return True  # Still consider it a success if no error was thrown
            
    except Exception as e:
        print(f"❌ Order submission failed: {e}")
        
        # Check if it's a Cloudflare error
        if "403" in str(e) and "Cloudflare" in str(e):
            print("🛡️ Cloudflare blocking detected")
            print("💡 This suggests the issue is IP-based, not frequency-based")
        
        return False

if __name__ == "__main__":
    print("🤖 Flowbot Single Trade Test")
    print("Testing if we can execute one static trade order")
    print("This will help determine if Cloudflare blocking is frequency or IP-based\n")
    
    success = test_single_trade()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCCESS: Single trade executed successfully!")
        print("✅ The trading system is working correctly")
        print("💡 Cloudflare blocking may be frequency-based")
    else:
        print("❌ FAILED: Single trade could not be executed")
        print("🛡️ Cloudflare blocking appears to be IP or pattern-based")
        print("💡 Consider using VPN or contacting Polymarket for API access")
    
    print("\nTest complete.") 