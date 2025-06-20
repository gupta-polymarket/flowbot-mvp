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
    
    def __init__(self, client: ClobClient, config: Dict[str, Any], max_spend_per_side: float = 2.0, buy_only: bool = False):
        self.client = client
        self.config = config
        self.max_spend_per_side = max_spend_per_side
        self.buy_only = buy_only
        self.session_trades = defaultdict(list)  # Track trades per market
        
        mode_desc = "BUY-ONLY (ask taking)" if buy_only else "BUY/SELL (bid and ask taking)"
        logger.info(f"Spread Tightening Bot initialized with max ${max_spend_per_side} per side, Mode: {mode_desc}")
    
    def get_orderbook_data(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get orderbook data for a token"""
        try:
            orderbook = self.client.get_order_book(token_id)
            
            if not orderbook.bids or not orderbook.asks:
                logger.debug(f"No orderbook data for token {token_id}")
                return None
            
            # Convert to dict format and ensure correct sorting
            # Bids should be sorted highest to lowest (descending by price)
            # Asks should be sorted lowest to highest (ascending by price)
            bids = [{'price': float(bid.price), 'size': float(bid.size)} for bid in orderbook.bids]
            asks = [{'price': float(ask.price), 'size': float(ask.size)} for ask in orderbook.asks]
            
            # Sort to ensure correct order (in case API doesn't return them sorted)
            bids.sort(key=lambda x: x['price'], reverse=True)  # Highest to lowest
            asks.sort(key=lambda x: x['price'])  # Lowest to highest
            
            return {
                'bids': bids,
                'asks': asks
            }
        except Exception as e:
            logger.error(f"Failed to get orderbook for {token_id}: {e}")
            return None
    
    def calculate_spread_info(self, orderbook: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Calculate current spread information"""
        best_bid = orderbook['bids'][0]['price']  # Highest buyer price
        best_ask = orderbook['asks'][0]['price']  # Lowest seller price
        
        # Sanity check: best bid should be less than best ask
        if best_bid >= best_ask:
            logger.error(f"Invalid orderbook: best_bid ({best_bid}) >= best_ask ({best_ask})")
            return None
        
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
    
    def find_optimal_taking_orders(self, orderbook: Dict[str, Any], spread_info: Dict[str, float], buy_only: bool = False) -> List[Dict[str, Any]]:
        """
        Find optimal orders to take that will tighten the spread by removing best bid/ask orders
        
        STRATEGY:
        - BID TAKING: Take bids starting from HIGHEST buyer price (best bid), moving it down
        - ASK TAKING: Take asks starting from LOWEST seller price (best ask), moving it up
        
        Args:
            orderbook: Current market orderbook (bids sorted high→low, asks sorted low→high)
            spread_info: Spread analysis data
            buy_only: If True, only take ask orders (BUY only)
        
        Returns list of order specifications with side, price, and size
        """
        orders_to_take = []
        
        if not buy_only:
            # 🔴 BID TAKING STRATEGY:
            # Take bids starting from BEST BID (highest buyer price)
            # Example: If bids are [14¢, 13¢, 12¢], we sell to 14¢ first, then 13¢
            # This removes high bidders and moves best bid from 14¢ → 13¢ → 12¢
            remaining_bid_budget = self.max_spend_per_side
            for bid in orderbook['bids']:  # Already sorted highest to lowest
                if remaining_bid_budget > 0:
                    max_shares = remaining_bid_budget / bid['price']
                    shares_to_take = min(max_shares, bid['size'])
                    cost = shares_to_take * bid['price']
                    
                    # Ensure we meet the $1.00 minimum exactly
                    if cost >= 1.0:  # Minimum order size
                        cost = max(1.0, round(cost, 2))
                        shares_to_take = cost / bid['price']  # Recalculate shares for exact cost
                        
                        orders_to_take.append({
                            'side': SELL,  # We sell to take their bid
                            'price': bid['price'],
                            'size': shares_to_take,
                            'cost': cost,
                            'type': 'bid_taking'
                        })
                        remaining_bid_budget -= cost
        
        # 🟢 ASK TAKING STRATEGY:
        # Take asks starting from BEST ASK (lowest seller price)  
        # Example: If asks are [16¢, 17¢, 18¢], we buy 16¢ first, then 17¢
        # This removes cheap sellers and moves best ask from 16¢ → 17¢ → 18¢
        ask_budget = self.max_spend_per_side * (2 if buy_only else 1)
        remaining_ask_budget = ask_budget
        
        for ask in orderbook['asks']:  # Already sorted lowest to highest
            if remaining_ask_budget > 0:
                max_shares = remaining_ask_budget / ask['price']
                shares_to_take = min(max_shares, ask['size'])
                cost = shares_to_take * ask['price']
                
                # Ensure we meet the $1.00 minimum exactly
                if cost >= 1.0:  # Minimum order size
                    # Round cost up to nearest cent to ensure we meet minimums
                    cost = max(1.0, round(cost, 2))
                    shares_to_take = cost / ask['price']  # Recalculate shares for exact cost
                    
                    orders_to_take.append({
                        'side': BUY,  # We buy to take their ask
                        'price': ask['price'],
                        'size': shares_to_take,
                        'cost': cost,
                        'type': 'ask_taking'
                    })
                    remaining_ask_budget -= cost
        
        return orders_to_take
    
    def display_orderbook_summary(self, orderbook: Dict[str, Any], spread_info: Dict[str, float]):
        """Display a summary of the current orderbook state"""
        print(f"💹 Best Bid: ${spread_info['best_bid']:.4f} (Size: {orderbook['bids'][0]['size']:.1f}) [HIGHEST buyer price]")
        print(f"💹 Best Ask: ${spread_info['best_ask']:.4f} (Size: {orderbook['asks'][0]['size']:.1f}) [LOWEST seller price]")
        print(f"📏 Spread: ${spread_info['spread']:.4f} ({spread_info['spread_pct']:.2f}%)")
        print(f"🎯 Mid Price: ${spread_info['mid_price']:.4f}")
        
        # Show top 5 bids and asks with clear labeling
        print("📖 Full Orderbook View:")
        print("   🟢 BIDS (buyers, highest to lowest):")
        for i, bid in enumerate(orderbook['bids'][:5]):
            marker = "👑" if i == 0 else f" {i+1}."
            print(f"      {marker} ${bid['price']:.4f} ({bid['size']:.1f} shares)")
        
        print("   🔴 ASKS (sellers, lowest to highest):")
        for i, ask in enumerate(orderbook['asks'][:5]):
            marker = "⭐" if i == 0 else f" {i+1}."
            print(f"      {marker} ${ask['price']:.4f} ({ask['size']:.1f} shares)")
    
    def find_optimal_taking_orders_with_budget(self, orderbook: Dict[str, Any], spread_info: Dict[str, float], max_budget: float) -> List[Dict[str, Any]]:
        """
        Find optimal orders to take within a specific budget constraint
        
        STRATEGY: Same as find_optimal_taking_orders but with budget limit
        - BID TAKING: Take bids from HIGHEST buyer price downward (14¢→13¢→12¢)
        - ASK TAKING: Take asks from LOWEST seller price upward (16¢→17¢→18¢)
        
        Args:
            orderbook: Current market orderbook (bids sorted high→low, asks sorted low→high)
            spread_info: Spread analysis data
            max_budget: Maximum budget for this round
        
        Returns list of order specifications with side, price, and size
        """
        orders_to_take = []
        remaining_budget = max_budget
        
        if not self.buy_only:
            # 🔴 BID TAKING: Remove highest bidders to move best bid down
            # Example: Bids [14¢, 13¢, 12¢] → sell to 14¢ first → best bid becomes 13¢
            for bid in orderbook['bids']:  # Already sorted highest to lowest
                if remaining_budget > 0:
                    max_shares = remaining_budget / bid['price']
                    shares_to_take = min(max_shares, bid['size'])
                    cost = shares_to_take * bid['price']
                    
                    # Ensure we meet the $1.00 minimum exactly  
                    if cost >= 1.0:  # Minimum order size
                        cost = max(1.0, round(cost, 2))
                        shares_to_take = cost / bid['price']  # Recalculate shares for exact cost
                        
                        orders_to_take.append({
                            'side': SELL,  # We sell to take their bid
                            'price': bid['price'],
                            'size': shares_to_take,
                            'cost': cost,
                            'type': 'bid_taking'
                        })
                        remaining_budget -= cost
                        
                        # In mixed mode, leave some budget for ask taking
                        if remaining_budget < max_budget * 0.4:
                            break
        
        # 🟢 ASK TAKING: Remove lowest sellers to move best ask up
        # Example: Asks [16¢, 17¢, 18¢] → buy 16¢ first → best ask becomes 17¢
        for ask in orderbook['asks']:  # Already sorted lowest to highest
            if remaining_budget > 0:
                max_shares = remaining_budget / ask['price']
                shares_to_take = min(max_shares, ask['size'])
                cost = shares_to_take * ask['price']
                
                # Ensure we meet the $1.00 minimum exactly
                if cost >= 1.0:  # Minimum order size
                    cost = max(1.0, round(cost, 2))
                    shares_to_take = cost / ask['price']  # Recalculate shares for exact cost
                    
                    orders_to_take.append({
                        'side': BUY,  # We buy to take their ask
                        'price': ask['price'],
                        'size': shares_to_take,
                        'cost': cost,
                        'type': 'ask_taking'
                    })
                    remaining_budget -= cost
        
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
    
    def process_market(self, token_id: str, max_budget: float = None) -> bool:
        """
        Process a single market for aggressive spread tightening
        Makes multiple rounds of trades until spread is significantly reduced or budget exhausted
        
        Args:
            token_id: The market token to trade
            max_budget: Maximum total budget for this market (default: $3.0)
        
        Returns True if any trades were executed
        """
        logger.info(f"Processing market for token {token_id}")
        
        # Set budget for this market
        market_budget = max_budget or 3.0  # Default $3 budget
        total_spent = 0.0
        round_number = 1
        
        market_info = get_market_info(token_id)
        mode_indicator = "🛒 BUY-ONLY MODE" if self.buy_only else "🔄 BUY/SELL MODE"
        
        print(f"\n🎯 AGGRESSIVE MARKET PROCESSING ({mode_indicator})")
        print(f"📊 Market: {market_info}")
        print(f"💰 Total Budget: ${market_budget:.2f}")
        print("=" * 70)
        
        any_trades_executed = False
        initial_spread = None
        
        while total_spent < market_budget:
            print(f"\n🔄 TRADING ROUND {round_number}")
            print(f"💰 Remaining Budget: ${market_budget - total_spent:.2f}")
            
            # Get current orderbook
            orderbook = self.get_orderbook_data(token_id)
            if not orderbook:
                print("❌ No orderbook data available")
                break
            
            # Calculate spread information
            spread_info = self.calculate_spread_info(orderbook)
            if not spread_info:
                print("❌ Unable to calculate spread information")
                break
            
            # Track initial spread for comparison
            if initial_spread is None:
                initial_spread = spread_info['spread']
            
            # Show BEFORE orderbook state
            print(f"\n📖 ORDERBOOK STATE (Round {round_number} - BEFORE)")
            print("-" * 50)
            self.display_orderbook_summary(orderbook, spread_info)
            
            # Skip if spread is already very tight
            min_spread = 0.005  # 0.5 cent minimum spread
            if spread_info['spread'] < min_spread:
                print(f"✅ Spread sufficiently tight (< ${min_spread:.3f}), mission accomplished!")
                break
            
            # Calculate remaining budget for this round
            remaining_budget = market_budget - total_spent
            round_budget = min(remaining_budget, 1.5)  # Max $1.50 per round
            
            # Find orders to take with current budget constraints
            orders_to_take = self.find_optimal_taking_orders_with_budget(
                orderbook, spread_info, round_budget
            )
            
            if not orders_to_take:
                print("ℹ️  No more profitable spread-tightening opportunities found")
                break
            
            print(f"\n🎯 Found {len(orders_to_take)} trading opportunities:")
            for i, order in enumerate(orders_to_take):
                print(f"  {i+1}. {order['side']} {order['size']:.1f} @ ${order['price']:.4f} (${order['cost']:.2f}) - {order['type']}")
            
            # Execute orders
            round_spent = 0.0
            executed_orders = 0
            
            for order in orders_to_take:
                if total_spent + round_spent + order['cost'] > market_budget:
                    print(f"💰 Would exceed budget, skipping order (${order['cost']:.2f})")
                    continue
                    
                success = self.execute_taking_order(token_id, order)
                if success:
                    executed_orders += 1
                    round_spent += order['cost']
                    self.session_trades[token_id].append({
                        'side': order['side'],
                        'price': order['price'],
                        'size': order['size'],
                        'cost': order['cost'],
                        'type': order['type'],
                        'round': round_number
                    })
                    # Brief pause between orders
                    time.sleep(1)
            
            total_spent += round_spent
            
            if executed_orders > 0:
                any_trades_executed = True
                print(f"\n✅ Round {round_number} Complete:")
                print(f"   Executed: {executed_orders} orders")
                print(f"   Spent: ${round_spent:.2f}")
                print(f"   Total Spent: ${total_spent:.2f} / ${market_budget:.2f}")
                
                # Show AFTER orderbook state
                print(f"\n📖 ORDERBOOK STATE (Round {round_number} - AFTER)")
                print("-" * 50)
                time.sleep(2)  # Wait for orders to settle
                updated_orderbook = self.get_orderbook_data(token_id)
                if updated_orderbook:
                    updated_spread_info = self.calculate_spread_info(updated_orderbook)
                    if updated_spread_info:
                        self.display_orderbook_summary(updated_orderbook, updated_spread_info)
                        
                        # Show improvement
                        old_spread = spread_info['spread']
                        new_spread = updated_spread_info['spread']
                        improvement = old_spread - new_spread
                        improvement_pct = (improvement / old_spread) * 100 if old_spread > 0 else 0
                        
                        print(f"\n📈 ROUND {round_number} IMPACT:")
                        print(f"   Spread Before: ${old_spread:.4f}")
                        print(f"   Spread After:  ${new_spread:.4f}")
                        print(f"   Improvement: ${improvement:.4f} ({improvement_pct:.1f}%)")
                
                round_number += 1
                
                # Brief pause between rounds
                if total_spent < market_budget and round_number <= 5:  # Max 5 rounds
                    print(f"⏳ Pausing 3 seconds before next round...")
                    time.sleep(3)
                else:
                    break
            else:
                print(f"❌ Round {round_number}: No orders executed")
                break
        
        # Final summary
        print(f"\n{'='*70}")
        print(f"📊 AGGRESSIVE MARKET PROCESSING COMPLETE")
        print(f"💰 Total Spent: ${total_spent:.2f} / ${market_budget:.2f}")
        print(f"🔄 Trading Rounds: {round_number - 1}")
        
        if initial_spread and any_trades_executed:
            # Get final spread
            final_orderbook = self.get_orderbook_data(token_id)
            if final_orderbook:
                final_spread_info = self.calculate_spread_info(final_orderbook)
                if final_spread_info:
                    final_spread = final_spread_info['spread']
                    total_improvement = initial_spread - final_spread
                    total_improvement_pct = (total_improvement / initial_spread) * 100
                    
                    print(f"📈 TOTAL IMPACT:")
                    print(f"   Initial Spread: ${initial_spread:.4f}")
                    print(f"   Final Spread:   ${final_spread:.4f}")
                    print(f"   Total Improvement: ${total_improvement:.4f} ({total_improvement_pct:.1f}%)")
        
        print(f"{'='*70}")
        
        return any_trades_executed
    
    def run_session(self, token_ids: List[str], iterations: Optional[int] = None, interval_range: Tuple[int, int] = (10, 20), market_budget: float = 3.0):
        """
        Run a spread tightening session
        
        Args:
            token_ids: List of token IDs to process
            iterations: Number of iterations (None for infinite)
            interval_range: (min, max) seconds between iterations
            market_budget: Budget per market for aggressive trading
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
                success = self.process_market(token_id, market_budget)
                
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
    parser.add_argument("--market-budget", type=float, default=3.0, help="Total budget per market for aggressive spread tightening (default: 3.0)")
    parser.add_argument("--buy-only", action="store_true", help="Only place BUY orders (take ask orders) to tighten spread from ask side (can also be set in config file)")
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
        mode_desc = " (BUY-ONLY)" if args.buy_only else ""
        print(f"🔍 DRY RUN MODE{mode_desc} - No real trades will be executed")
    
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
    
    # Get buy_only setting from command line or config file
    buy_only = args.buy_only or config.get("buy_only", False)
    
    # Create and run the taker bot
    taker_bot = SpreadTighteningBot(client, config, args.max_spend, buy_only)
    taker_bot.run_session(
        token_ids=token_ids,
        iterations=args.iterations,
        interval_range=(args.min_interval, args.max_interval),
        market_budget=args.market_budget
    )


if __name__ == "__main__":
    main() 