#!/usr/bin/env python3
"""
Test Price Filtering - Demonstrate the new price filtering functionality
"""
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from flowbot.config import load_config

def test_price_filtering():
    """Test the price filtering functionality"""
    print("🎯 Testing Price Filtering (10¢ - 90¢)")
    print("=" * 50)
    
    # Load environment and config
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    funding_address = os.getenv("FUNDING_ADDRESS")
    config = load_config()
    
    if not private_key or not funding_address:
        print("❌ Missing PRIVATE_KEY or FUNDING_ADDRESS")
        return False
    
    print(f"📊 Price range: ${config['min_price']:.2f} - ${config['max_price']:.2f}")
    
    # Setup client
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=private_key,
        chain_id=137,
        signature_type=1,
        funder=funding_address
    )
    client.set_api_creds(client.create_or_derive_api_creds())
    print("✅ Client setup complete")
    
    # Test a few different tokens to see price filtering in action
    test_tokens = [
        "71685983838843709915160975671540060908877886707703474939962098991499689519711",  # Ukraine NATO
        "90863997347884468057633285822709973829164736268814958635981051330892926102120",   # Letitia James
        "106421420997567331154928145134345171536002132387398066094504839176677088790706",  # Khamenei
    ]
    
    print(f"\n🧪 Testing {len(test_tokens)} markets for price filtering...")
    
    valid_markets = 0
    filtered_markets = 0
    
    for i, token_id in enumerate(test_tokens):
        print(f"\n📊 Market {i+1}:")
        
        try:
            # Get orderbook
            orderbook = client.get_order_book(token_id)
            
            if orderbook.asks and orderbook.bids:
                ask_price = float(orderbook.asks[0].price)
                bid_price = float(orderbook.bids[0].price)
                
                print(f"   💰 Ask: ${ask_price:.4f}, Bid: ${bid_price:.4f}")
                
                # Check if ask price is in range (for BUY orders)
                min_price = config['min_price']
                max_price = config['max_price']
                
                if min_price <= ask_price <= max_price:
                    print(f"   ✅ Ask price ${ask_price:.4f} is in range ${min_price:.2f}-${max_price:.2f}")
                    valid_markets += 1
                else:
                    print(f"   ❌ Ask price ${ask_price:.4f} outside range ${min_price:.2f}-${max_price:.2f}")
                    filtered_markets += 1
                
                if min_price <= bid_price <= max_price:
                    print(f"   ✅ Bid price ${bid_price:.4f} is in range ${min_price:.2f}-${max_price:.2f}")
                else:
                    print(f"   ❌ Bid price ${bid_price:.4f} outside range ${min_price:.2f}-${max_price:.2f}")
                    
            else:
                print(f"   ⚠️  No orderbook data available")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Price Filtering Results:")
    print(f"✅ Markets in range: {valid_markets}")
    print(f"❌ Markets filtered out: {filtered_markets}")
    print(f"📈 This will help focus on markets with better liquidity!")
    
    print(f"\n💡 How it works:")
    print("- Bot checks price before placing orders")
    print("- Skips markets with extreme prices (< 10¢ or > 90¢)")
    print("- Focuses on markets with reasonable spreads")
    print("- Improves trading efficiency")

if __name__ == "__main__":
    test_price_filtering() 