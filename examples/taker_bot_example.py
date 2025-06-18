#!/usr/bin/env python3
"""
Example: Using the Taker Bot programmatically

This example shows how to use the SpreadTighteningBot class
in your own scripts for custom spread tightening strategies.
"""

import sys
import os

# Add the parent directory to the path so we can import flowbot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flowbot import SpreadTighteningBot, load_config
from flowbot.bot import setup_clob_client, get_active_markets_from_gamma, validate_token_id


def example_basic_usage():
    """Basic example: Run taker bot on random markets"""
    print("🎯 Basic Taker Bot Example")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    
    # Setup CLOB client
    print("Setting up CLOB client...")
    client = setup_clob_client()
    
    # Get active markets
    print("Discovering active markets...")
    token_ids = get_active_markets_from_gamma()
    token_ids = [tid for tid in token_ids if validate_token_id(tid)]
    
    print(f"Found {len(token_ids)} active markets")
    
    # Create taker bot with $1.50 max spend per side
    taker_bot = SpreadTighteningBot(client, config, max_spend_per_side=1.5)
    
    # Run for 3 iterations with 20-30 second intervals
    print("Starting spread tightening session...")
    taker_bot.run_session(
        token_ids=token_ids[:10],  # Use first 10 markets
        iterations=3,
        interval_range=(20, 30)
    )


def example_specific_markets():
    """Example: Target specific markets by URL"""
    print("🎯 Specific Markets Example")
    print("=" * 50)
    
    # Define target markets
    market_urls = [
        "https://polymarket.com/event/presidential-election-winner",
        "https://polymarket.com/event/bitcoin-100k-2024"
    ]
    
    # Load configuration
    config = load_config()
    config["manual_approval"] = True  # Ensure manual approval for this example
    
    # Setup CLOB client
    print("Setting up CLOB client...")
    client = setup_clob_client()
    
    # Resolve URLs to token IDs
    print("Resolving market URLs...")
    from flowbot.taker_bot import resolve_market_urls_to_tokens
    token_ids = resolve_market_urls_to_tokens(market_urls)
    
    print(f"Resolved to {len(token_ids)} token IDs")
    
    # Create taker bot with $2 max spend per side
    taker_bot = SpreadTighteningBot(client, config, max_spend_per_side=2.0)
    
    # Run for 5 iterations
    print("Starting targeted spread tightening...")
    taker_bot.run_session(
        token_ids=token_ids,
        iterations=5,
        interval_range=(30, 60)
    )


def example_custom_strategy():
    """Example: Custom spread analysis strategy"""
    print("🎯 Custom Strategy Example")
    print("=" * 50)
    
    config = load_config()
    client = setup_clob_client()
    
    # Create taker bot
    taker_bot = SpreadTighteningBot(client, config, max_spend_per_side=2.0)
    
    # Get a single market for detailed analysis
    token_ids = get_active_markets_from_gamma()
    token_ids = [tid for tid in token_ids if validate_token_id(tid)]
    
    if not token_ids:
        print("No active markets found")
        return
    
    token_id = token_ids[0]
    
    # Get orderbook data
    print(f"Analyzing market: {token_id}")
    orderbook = taker_bot.get_orderbook_data(token_id)
    
    if not orderbook:
        print("No orderbook data available")
        return
    
    # Calculate spread information
    spread_info = taker_bot.calculate_spread_info(orderbook)
    
    print(f"Best Bid: ${spread_info['best_bid']:.4f}")
    print(f"Best Ask: ${spread_info['best_ask']:.4f}")
    print(f"Spread: ${spread_info['spread']:.4f} ({spread_info['spread_pct']:.2f}%)")
    print(f"Mid Price: ${spread_info['mid_price']:.4f}")
    
    # Find optimal orders to take
    orders_to_take = taker_bot.find_optimal_taking_orders(orderbook, spread_info)
    
    print(f"\nFound {len(orders_to_take)} potential orders to take:")
    for i, order in enumerate(orders_to_take):
        print(f"  {i+1}. {order['side']} {order['size']:.2f} @ ${order['price']:.4f} (${order['cost']:.2f})")
    
    # You could process the market if desired
    # success = taker_bot.process_market(token_id)


def example_dry_run():
    """Example: Analyze markets without trading"""
    print("🎯 Dry Run Example")
    print("=" * 50)
    
    config = load_config()
    config["manual_approval"] = False  # No approval needed for dry run
    
    # For dry run, we don't need a real client
    # But we still need token IDs
    token_ids = get_active_markets_from_gamma()
    token_ids = [tid for tid in token_ids if validate_token_id(tid)]
    
    print(f"Would analyze {len(token_ids)} markets")
    print("Markets to analyze:")
    
    from flowbot.bot import get_market_info
    for i, token_id in enumerate(token_ids[:5]):  # Show first 5
        market_info = get_market_info(token_id)
        print(f"  {i+1}. {market_info}")
    
    if len(token_ids) > 5:
        print(f"  ... and {len(token_ids) - 5} more markets")
    
    print("\nTo run for real, use one of the other examples!")


if __name__ == "__main__":
    print("Flowbot Taker Bot Examples")
    print("=" * 50)
    print("1. Basic usage (random markets)")
    print("2. Specific markets (by URL)")
    print("3. Custom strategy analysis")
    print("4. Dry run (analysis only)")
    print()
    
    choice = input("Choose an example (1-4): ").strip()
    
    try:
        if choice == "1":
            example_basic_usage()
        elif choice == "2":
            example_specific_markets()
        elif choice == "3":
            example_custom_strategy()
        elif choice == "4":
            example_dry_run()
        else:
            print("Invalid choice. Please run again and choose 1-4.")
    except KeyboardInterrupt:
        print("\n🛑 Example stopped by user")
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc() 