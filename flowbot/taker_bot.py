#!/usr/bin/env python3
"""
Taker Bot - Spread Tightening Bot for Polymarket

This bot specializes in tightening spreads by taking the best bid and ask orders
up to $2 on each side. It can work with specific market URLs or randomly select
active markets.
"""

import argparse
import logging
import time
import random
import json
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict

import requests
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType

try:
    from py_clob_client.order_builder.constants import BUY, SELL
except ImportError:
    BUY, SELL = "BUY", "SELL"

from flowbot.config import load_config
from flowbot.bot import (
    setup_clob_client, 
    resolve_url_to_token_ids,
    get_active_markets_from_gamma,
    get_market_info,
    validate_token_id
)

# Configure logging
logger = logging.getLogger("flowbot.taker")


class SpreadTighteningBot:
    """
    A specialized bot that tightens spreads by taking best bid/ask orders
    """
    
    def __init__(self, client: ClobClient, config: Dict[str, Any], max_spend_per_side: float = 2.0):
        self.client = client
        self.config = config
        self.max_spend_per_side = max_spend_per_side
        self.session_trades = defaultdict(list)  # Track trades per market
        
        logger.info(f"Spread Tightening Bot initialized with max ${max_spend_per_side} per side")
    
    def get_orderbook_data(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get orderbook data for a token"""
        try:
            orderbook = self.client.get_order_book(token_id)
            
            if not orderbook.bids or not orderbook.asks:
                logger.debug(f"No orderbook data for token {token_id}")
                return None
            
            # Convert to dict format for easier processing
            return {
                'bids': [{'price': float(bid.price), 'size': float(bid.size)} for bid in orderbook.bids],
                'asks': [{'price': float(ask.price), 'size': float(ask.size)} for ask in orderbook.asks]
            }
        except Exception as e:
            logger.error(f"Failed to get orderbook for {token_id}: {e}")
            return None
    
    def calculate_spread_info(self, orderbook: Dict[str, Any]) -> Dict[str, float]:
        """Calculate current spread information"""
        best_bid = orderbook['bids'][0]['price']
        best_ask = orderbook['asks'][0]['price']
        
        spread = best_ask - best_bid
        spread_pct = (spread / ((best_bid + best_ask) / 2)) * 100
        mid_price = (best_bid + best_ask) / 2
        
        return {
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': spread,
            'spread_pct': spread_pct,
            'mid_price': mid_price
        }
    
    def find_optimal_taking_orders(self, orderbook: Dict[str, Any], spread_info: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Find optimal orders to take that will tighten the spread
        
        Returns list of order specifications with side, price, and size
        """
        orders_to_take = []
        
        # Calculate how much we want to improve the spread
        current_spread = spread_info['spread']
        mid_price = spread_info['mid_price']
        
        # Target: improve spread by taking orders that are close to mid-price
        # We'll take bids above 25% of the way from current best bid to mid
        # And take asks below 25% of the way from current best ask to mid
        
        bid_threshold = spread_info['best_bid'] + (current_spread * 0.25)
        ask_threshold = spread_info['best_ask'] - (current_spread * 0.25)
        
        # Find bid orders to take (sell to these bids)
        remaining_bid_budget = self.max_spend_per_side
        for bid in orderbook['bids']:
            if bid['price'] >= bid_threshold and remaining_bid_budget > 0:
                # Calculate how much we can take
                max_shares = remaining_bid_budget / bid['price']
                shares_to_take = min(max_shares, bid['size'])
                cost = shares_to_take * bid['price']
                
                if cost >= 1.0:  # Minimum order size
                    orders_to_take.append({
                        'side': SELL,  # We sell to take their bid
                        'price': bid['price'],
                        'size': shares_to_take,
                        'cost': cost,
                        'type': 'bid_taking'
                    })
                    remaining_bid_budget -= cost
        
        # Find ask orders to take (buy from these asks)
        remaining_ask_budget = self.max_spend_per_side
        for ask in orderbook['asks']:
            if ask['price'] <= ask_threshold and remaining_ask_budget > 0:
                # Calculate how much we can take
                max_shares = remaining_ask_budget / ask['price']
                shares_to_take = min(max_shares, ask['size'])
                cost = shares_to_take * ask['price']
                
                if cost >= 1.0:  # Minimum order size
                    orders_to_take.append({
                        'side': BUY,  # We buy to take their ask
                        'price': ask['price'],
                        'size': shares_to_take,
                        'cost': cost,
                        'type': 'ask_taking'
                    })
                    remaining_ask_budget -= cost
        
        return orders_to_take
    
    def execute_taking_order(self, token_id: str, order_spec: Dict[str, Any]) -> bool:
        """Execute a single taking order"""
        try:
            side = order_spec['side']
            price = order_spec['price']
            size = order_spec['size']
            cost = order_spec['cost']
            order_type = order_spec['type']
            
            # Get market info for display
            market_info = get_market_info(token_id)
            
            print(f"\n📈 SPREAD TIGHTENING ORDER")
            print(f"📊 Market: {market_info}")
            print(f"🎯 Strategy: {order_type}")
            print(f"📋 Action: {side}")
            print(f"💰 Price: ${price:.4f}")
            print(f"📦 Size: {size:.2f} shares")
            print(f"💵 Cost: ${cost:.2f}")
            
            # Manual approval if enabled
            if self.config.get("manual_approval", False):
                while True:
                    approval = input("🤔 Execute this spread-tightening order? (y/n/q): ").lower().strip()
                    if approval == 'y':
                        print("✅ Order approved!")
                        break
                    elif approval == 'n':
                        print("❌ Order skipped")
                        return False
                    elif approval == 'q':
                        print("🛑 Quitting...")
                        exit(0)
                    else:
                        print("Please enter 'y', 'n', or 'q'")
            
            # Check for negative risk markets
            try:
                neg_risk_response = requests.get(f"https://clob.polymarket.com/neg-risk?token_id={token_id}", timeout=5)
                is_neg_risk = neg_risk_response.status_code == 200 and neg_risk_response.json().get("negRisk", False)
            except:
                is_neg_risk = False
            
            # Create order arguments
            order_args = OrderArgs(
                price=price,
                size=size,
                side=side,
                token_id=token_id
            )
            
            if is_neg_risk:
                try:
                    order_args.negrisk = True
                except:
                    logger.debug("Client doesn't support negrisk parameter")
            
            # Create and submit order
            signed_order = self.client.create_order(order_args)
            response = self.client.post_order(signed_order, OrderType.GTC)
            
            # Log successful trade
            trade_info = {
                'token_id': token_id,
                'side': side,
                'price': price,
                'size': size,
                'cost': cost,
                'type': order_type,
                'timestamp': time.time()
            }
            self.session_trades[token_id].append(trade_info)
            
            print(f"✅ Order executed successfully!")
            if hasattr(response, 'orderId'):
                print(f"Order ID: {response.orderId}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute taking order: {e}")
            print(f"❌ Order failed: {e}")
            return False
    
    def process_market(self, token_id: str) -> bool:
        """
        Process a single market for spread tightening opportunities
        
        Returns True if any orders were executed
        """
        logger.info(f"Processing market for token {token_id}")
        
        # Get orderbook data
        orderbook = self.get_orderbook_data(token_id)
        if not orderbook:
            logger.warning(f"No orderbook data for {token_id}")
            return False
        
        # Calculate spread information
        spread_info = self.calculate_spread_info(orderbook)
        
        # Display current market state
        market_info = get_market_info(token_id)
        print(f"\n🎯 ANALYZING MARKET")
        print(f"📊 Market: {market_info}")
        print(f"💹 Best Bid: ${spread_info['best_bid']:.4f}")
        print(f"💹 Best Ask: ${spread_info['best_ask']:.4f}")
        print(f"📏 Spread: ${spread_info['spread']:.4f} ({spread_info['spread_pct']:.2f}%)")
        print(f"🎯 Mid Price: ${spread_info['mid_price']:.4f}")
        
        # Skip if spread is already very tight
        if spread_info['spread'] < 0.01:  # Less than 1 cent spread
            print("✅ Spread already very tight, skipping")
            return False
        
        # Find orders to take
        orders_to_take = self.find_optimal_taking_orders(orderbook, spread_info)
        
        if not orders_to_take:
            print("ℹ️  No profitable spread-tightening opportunities found")
            return False
        
        print(f"🎯 Found {len(orders_to_take)} spread-tightening opportunities")
        
        # Execute orders
        executed_count = 0
        for order_spec in orders_to_take:
            if self.execute_taking_order(token_id, order_spec):
                executed_count += 1
                # Small delay between orders
                time.sleep(1)
        
        if executed_count > 0:
            print(f"✅ Successfully executed {executed_count} spread-tightening orders")
            return True
        else:
            print("❌ No orders were executed")
            return False
    
    def run_session(self, token_ids: List[str], iterations: Optional[int] = None, interval_range: Tuple[int, int] = (10, 20)):
        """
        Run a spread tightening session
        
        Args:
            token_ids: List of token IDs to process
            iterations: Number of iterations (None for infinite)
            interval_range: (min, max) seconds between iterations
        """
        logger.info(f"Starting spread tightening session with {len(token_ids)} markets")
        
        iteration = 0
        try:
            while iterations is None or iteration < iterations:
                iteration += 1
                print(f"\n{'='*60}")
                print(f"🎯 SPREAD TIGHTENING ITERATION {iteration}")
                print(f"{'='*60}")
                
                # Randomly select a market from the list
                token_id = random.choice(token_ids)
                
                # Process the market
                success = self.process_market(token_id)
                
                # Show session statistics
                total_trades = sum(len(trades) for trades in self.session_trades.values())
                markets_traded = len(self.session_trades)
                
                print(f"\n📊 SESSION STATS")
                print(f"Iteration: {iteration}")
                print(f"Total trades: {total_trades}")
                print(f"Markets traded: {markets_traded}")
                
                # Wait before next iteration (unless this is the last one)
                if iterations is None or iteration < iterations:
                    wait_time = random.randint(*interval_range)
                    print(f"⏰ Waiting {wait_time} seconds until next iteration...")
                    time.sleep(wait_time)
                
        except KeyboardInterrupt:
            print("\n🛑 Session stopped by user")
        except Exception as e:
            logger.error(f"Session error: {e}")
            print(f"❌ Session error: {e}")
        
        # Final session summary
        self.print_session_summary()
    
    def print_session_summary(self):
        """Print a summary of the trading session"""
        print(f"\n{'='*60}")
        print(f"📊 FINAL SESSION SUMMARY")
        print(f"{'='*60}")
        
        total_trades = 0
        total_volume = 0.0
        
        for token_id, trades in self.session_trades.items():
            if trades:
                market_info = get_market_info(token_id)
                market_volume = sum(trade['cost'] for trade in trades)
                
                print(f"\n🎯 {market_info}")
                print(f"   Trades: {len(trades)}")
                print(f"   Volume: ${market_volume:.2f}")
                
                total_trades += len(trades)
                total_volume += market_volume
        
        print(f"\n🎯 TOTALS")
        print(f"Markets: {len(self.session_trades)}")
        print(f"Trades: {total_trades}")
        print(f"Volume: ${total_volume:.2f}")
        print(f"{'='*60}")


def resolve_market_urls_to_tokens(urls: List[str]) -> List[str]:
    """
    Resolve a list of Polymarket URLs to token IDs
    
    Args:
        urls: List of Polymarket URLs
        
    Returns:
        List of unique token IDs
    """
    logger.info(f"Resolving {len(urls)} market URLs to token IDs")
    
    all_tokens = set()
    clob_host = "https://clob.polymarket.com"
    
    for url in urls:
        try:
            tokens = resolve_url_to_token_ids(url, clob_host)
            all_tokens.update(tokens)
            logger.info(f"✅ {url} -> {len(tokens)} tokens")
        except Exception as e:
            logger.error(f"❌ Failed to resolve {url}: {e}")
            continue
    
    result = list(all_tokens)
    logger.info(f"Resolved to {len(result)} unique token IDs")
    return result


def main():
    """Main entry point for the taker bot"""
    parser = argparse.ArgumentParser(description="Polymarket Spread Tightening Bot")
    parser.add_argument("--markets", nargs="+", help="Market URLs to target (if not provided, random markets will be used)")
    parser.add_argument("--token-ids", nargs="+", help="Specific token IDs to target directly")
    parser.add_argument("--max-spend", type=float, default=2.0, help="Maximum spend per side in USDC (default: 2.0)")
    parser.add_argument("--iterations", type=int, help="Number of iterations to run (default: infinite)")
    parser.add_argument("--min-interval", type=int, default=10, help="Minimum seconds between iterations")
    parser.add_argument("--max-interval", type=int, default=20, help="Maximum seconds between iterations")
    parser.add_argument("--dry-run", action="store_true", help="Simulate trades without executing")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Override manual approval for dry runs
    if args.dry_run:
        config["manual_approval"] = False
        print("🔍 DRY RUN MODE - No real trades will be executed")
    
    # Setup CLOB client
    if not args.dry_run:
        client = setup_clob_client()
    else:
        client = None
    
    # Determine token IDs to trade
    token_ids = []
    
    if args.token_ids:
        print(f"🎯 Using provided token IDs: {len(args.token_ids)} tokens")
        token_ids = [tid for tid in args.token_ids if validate_token_id(tid)]
        print(f"✅ Validated {len(token_ids)} token IDs")
        
    elif args.markets:
        print(f"🎯 Using provided markets: {len(args.markets)} URLs")
        token_ids = resolve_market_urls_to_tokens(args.markets)
        
    else:
        print("🎲 No markets or token IDs provided, discovering active markets...")
        token_ids = get_active_markets_from_gamma()
        
        # Filter to valid token IDs
        token_ids = [tid for tid in token_ids if validate_token_id(tid)]
        
        if not token_ids:
            print("❌ No active markets found")
            return
    
    if not token_ids:
        print("❌ No valid token IDs found")
        return
    
    print(f"🎯 Will trade on {len(token_ids)} token IDs")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - Would analyze these markets:")
        for i, token_id in enumerate(token_ids[:5]):  # Show first 5
            market_info = get_market_info(token_id)
            print(f"  {i+1}. {market_info} (Token: {token_id[:20]}...)")
        if len(token_ids) > 5:
            print(f"  ... and {len(token_ids) - 5} more markets")
        print("\nTo run for real, remove the --dry-run flag")
        return
    
    # Create and run the taker bot
    taker_bot = SpreadTighteningBot(client, config, args.max_spend)
    taker_bot.run_session(
        token_ids=token_ids,
        iterations=args.iterations,
        interval_range=(args.min_interval, args.max_interval)
    )


if __name__ == "__main__":
    main() 