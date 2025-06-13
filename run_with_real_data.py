#!/usr/bin/env python3
"""
Run Flowbot with real market data but without executing actual trades
"""
import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowbot.bot import (
    setup_client, resolve_market_identifiers, get_best_price,
    sample_market, sample_side, sample_quantity, logger
)
from flowbot.config import load_config
from dotenv import load_dotenv

def run_real_data_demo():
    """Run the bot with real market data but no actual trades"""
    print("🚀 Flowbot - Real Market Data Demo")
    print("=" * 60)
    print("This shows what the bot would do with REAL market data")
    print("NO ACTUAL TRADES will be executed - this is for demonstration")
    print("=" * 60)
    
    # Load environment and config
    load_dotenv()
    config = load_config()
    
    # Set up fake credentials for demo (32 bytes = 64 hex chars)
    os.environ["PRIVATE_KEY"] = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    clob_host = os.getenv("CLOB_API_URL", "https://clob.polymarket.com")
    
    try:
        # Resolve markets
        raw_markets = config.get("markets", [])
        if not raw_markets:
            print("❌ No markets configured in config.yaml")
            return
        
        print(f"📊 Resolving {len(raw_markets)} market(s)...")
        resolved_tokens = resolve_market_identifiers(raw_markets, clob_host)
        config["markets"] = resolved_tokens
        
        print(f"✅ Resolved to {len(resolved_tokens)} token IDs")
        for i, token_id in enumerate(resolved_tokens):
            print(f"   {i+1}. {token_id}")
        
        # Set up client (we'll use it to fetch orderbooks but not trade)
        print("\n🔧 Setting up CLOB client...")
        client = setup_client(
            os.environ["PRIVATE_KEY"], 
            clob_host, 
            os.getenv("FUNDING_ADDRESS")
        )
        print("✅ Client setup complete")
        
        # Run a few iterations to show real data
        print(f"\n🎯 Running 3 iterations with REAL market data...")
        print("=" * 60)
        
        for iteration in range(1, 4):
            print(f"\n--- Iteration {iteration} ---")
            
            # Sample parameters
            token_id = sample_market(config)
            side = sample_side(config)
            quantity = sample_quantity(config)
            
            print(f"🎲 Sampled: token_id={token_id[:20]}..., side={side}, quantity={quantity}")
            
            # Get REAL orderbook
            print("📈 Fetching real orderbook...")
            try:
                orderbook = client.get_order_book(token_id)
                
                if not orderbook:
                    print("❌ Empty orderbook, would skip this iteration")
                    continue
                
                # Show orderbook data
                asks = orderbook.get("asks", [])
                bids = orderbook.get("bids", [])
                
                print(f"📊 Orderbook data:")
                print(f"   Best ask: {asks[0]['price'] if asks else 'None'} (size: {asks[0]['size'] if asks else 'None'})")
                print(f"   Best bid: {bids[0]['price'] if bids else 'None'} (size: {bids[0]['size'] if bids else 'None'})")
                
                # Get best price for our side
                price = get_best_price(orderbook, side)
                if price is None:
                    print(f"❌ No liquidity on {side} side, would skip")
                    continue
                
                print(f"💰 Best {side} price: {price}")
                
                # Calculate cost
                cost_usdc = quantity * price
                max_spend = float(config.get("max_spend_per_market", 5.0))
                
                print(f"💵 Trade details:")
                print(f"   Side: {side}")
                print(f"   Quantity: {quantity}")
                print(f"   Price: {price}")
                print(f"   Cost: {cost_usdc:.4f} USDC")
                print(f"   Budget remaining: {max_spend:.2f} USDC")
                
                if side == "BUY" and cost_usdc > max_spend:
                    scaled_qty = round(max_spend / price, 2)
                    scaled_cost = scaled_qty * price
                    print(f"⚖️  Would scale quantity from {quantity} to {scaled_qty} to fit budget")
                    print(f"   New cost: {scaled_cost:.4f} USDC")
                    quantity = scaled_qty
                    cost_usdc = scaled_cost
                
                print(f"🎯 WOULD EXECUTE: {side} {quantity} @ {price} ({cost_usdc:.4f} USDC)")
                print(f"   Order type: Fill-or-Kill (FOK)")
                print(f"   Expected: {'Take liquidity' if side == 'BUY' else 'Take liquidity'}")
                
            except Exception as e:
                print(f"❌ Error fetching orderbook: {e}")
                continue
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("\n🔥 The bot is ready to trade with REAL money!")
        print("\n⚠️  To run with actual trades:")
        print("1. Set your real PRIVATE_KEY in .env")
        print("2. Fund your account with USDC")
        print("3. Run: python -m flowbot.bot")
        print("4. Monitor logs carefully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_real_data_demo() 