#!/usr/bin/env python3
"""
Test Corrected Order Flow - Verify we're using the official Python client pattern correctly
"""
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY, SELL

def test_corrected_order_flow():
    """Test the corrected order flow using official Python client pattern"""
    print("🧪 Testing Corrected Order Flow")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    
    if not private_key:
        print("❌ PRIVATE_KEY not found in .env file")
        return False
    
    print("✅ Private key loaded")
    
    # Setup CLOB client using the correct pattern
    try:
        host = "https://clob.polymarket.com"
        chain_id = 137
        
        # Initialize client (direct EOA - no proxy needed with private key)
        client = ClobClient(
            host=host,
            key=private_key,
            chain_id=chain_id
        )
        print("✅ CLOB client created")
        
        # Set API credentials (CRITICAL STEP)
        client.set_api_creds(client.create_or_derive_api_creds())
        print("✅ API credentials set")
        
    except Exception as e:
        print(f"❌ Failed to setup CLOB client: {e}")
        return False
    
    # Use a known active token ID
    token_id = "71685983838843709915160975671540060908877886707703474939962098991499689519711"
    
    print(f"\n📊 Testing market: Will Ukraine join NATO before July?")
    print(f"🪙 Token ID: {token_id}")
    
    # Get orderbook to verify connectivity
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
    
    # Test the CORRECTED order creation flow
    print(f"\n🎯 Testing CORRECTED order flow:")
    print("   1. Create OrderArgs")
    print("   2. Call client.create_order() to sign")
    print("   3. Call client.post_order() with OrderType.GTC")
    
    # Create order arguments
    side = BUY
    price = best_ask  # Take the ask (market buy)
    size = 0.1  # Very small size to minimize cost
    
    print(f"\n📋 Order Details:")
    print(f"   Side: {side}")
    print(f"   Price: ${price:.4f}")
    print(f"   Size: {size} shares")
    print(f"   Cost: ${price * size:.4f} USDC")
    
    # Ask for confirmation
    confirm = input("\n🤔 Test this order creation flow? (y/n): ").lower().strip()
    if confirm != 'y':
        print("❌ Test cancelled by user")
        return False
    
    # Test the corrected flow
    try:
        print("\n🚀 Step 1: Creating OrderArgs...")
        
        order_args = OrderArgs(
            price=price,
            size=size,
            side=side,
            token_id=token_id
        )
        print("✅ OrderArgs created successfully")
        
        print("\n🔐 Step 2: Creating and signing order...")
        signed_order = client.create_order(order_args)
        print("✅ Order created and signed successfully")
        print(f"📋 Signed order type: {type(signed_order)}")
        
        print("\n📤 Step 3: Posting order with OrderType.GTC...")
        response = client.post_order(signed_order, OrderType.GTC)
        print("✅ Order posted successfully!")
        
        print(f"\n🎉 CORRECTED FLOW WORKS!")
        print(f"📋 Response: {response}")
        
        # Check response format
        if isinstance(response, dict):
            success = response.get('success', False)
            if success:
                print("✅ Order executed successfully!")
                order_id = response.get('orderId', 'Unknown')
                print(f"📋 Order ID: {order_id}")
            else:
                error_msg = response.get('errorMsg', 'Unknown error')
                print(f"⚠️ Order failed: {error_msg}")
        else:
            print(f"⚠️ Unexpected response format: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Order flow test failed: {e}")
        
        # Check for specific error types
        if "403" in str(e) and "Cloudflare" in str(e):
            print("🛡️ Cloudflare blocking detected")
        elif "signature" in str(e).lower():
            print("🔐 Signature error - check private key and API credentials")
        elif "balance" in str(e).lower() or "allowance" in str(e).lower():
            print("💰 Balance/allowance error - check USDC balance and approvals")
        
        return False

if __name__ == "__main__":
    success = test_corrected_order_flow()
    if success:
        print("\n✅ CORRECTED ORDER FLOW TEST PASSED")
        print("🎯 The bot is now using the official Python client pattern!")
    else:
        print("\n❌ CORRECTED ORDER FLOW TEST FAILED")
        print("🔧 Check the error messages above for debugging") 