#!/usr/bin/env python3
"""
Market Maker Module - Provides liquidity through structured limit orders

This module implements a market making strategy that:
1. Places limit orders away from current market prices
2. Provides liquidity for price discovery
3. Uses structured pricing to improve market efficiency
4. Manages risk through position limits and order cancellation
"""
import os
import sys
import time
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import json

import requests
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY, SELL

# Configure logging
logger = logging.getLogger('flowbot.market_maker')

class MarketMaker:
    """
    Market Making Engine for Polymarket CLOB
    
    Provides liquidity through structured limit orders that:
    - Improve bid-ask spreads
    - Facilitate price discovery
    - Generate trading fees through market making
    """
    
    def __init__(self, client: ClobClient, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.active_orders = {}  # Track our active orders
        self.positions = {}      # Track our positions per market
        
        # Market making parameters
        self.order_size = config.get('market_maker', {}).get('order_size', 1.0)
        self.spread_target = config.get('market_maker', {}).get('spread_target', 0.02)  # 2% spread
        self.max_position = config.get('market_maker', {}).get('max_position', 10.0)
        self.price_levels = config.get('market_maker', {}).get('price_levels', 3)
        self.order_refresh_interval = config.get('market_maker', {}).get('refresh_interval', 30)
        
        logger.info(f"Market Maker initialized with order_size=${self.order_size}, spread_target={self.spread_target*100}%")
    
    def get_fair_value(self, token_id: str) -> Optional[float]:
        """
        Estimate fair value for a token using multiple methods
        
        Args:
            token_id: Token to evaluate
            
        Returns:
            Estimated fair value or None if unable to determine
        """
        try:
            # Get current orderbook
            orderbook = self.client.get_order_book(token_id)
            
            if not orderbook.bids or not orderbook.asks:
                logger.warning(f"No orderbook data for token {token_id}")
                return None
            
            best_bid = float(orderbook.bids[0].price)
            best_ask = float(orderbook.asks[0].price)
            
            # Method 1: Mid-price
            mid_price = (best_bid + best_ask) / 2
            
            # Method 2: Volume-weighted mid (if we have size data)
            if hasattr(orderbook.bids[0], 'size') and hasattr(orderbook.asks[0], 'size'):
                bid_size = float(orderbook.bids[0].size)
                ask_size = float(orderbook.asks[0].size)
                total_size = bid_size + ask_size
                
                if total_size > 0:
                    vwap = (best_bid * ask_size + best_ask * bid_size) / total_size
                    # Blend mid-price and VWAP
                    fair_value = 0.7 * mid_price + 0.3 * vwap
                else:
                    fair_value = mid_price
            else:
                fair_value = mid_price
            
            logger.debug(f"Fair value for {token_id}: ${fair_value:.4f} (bid: ${best_bid:.4f}, ask: ${best_ask:.4f})")
            return fair_value
            
        except Exception as e:
            logger.error(f"Failed to get fair value for {token_id}: {e}")
            return None
    
    def calculate_quote_prices(self, fair_value: float, spread: float) -> Tuple[float, float]:
        """
        Calculate bid and ask prices based on fair value and target spread
        
        Args:
            fair_value: Estimated fair value
            spread: Target spread (as decimal, e.g., 0.02 for 2%)
            
        Returns:
            Tuple of (bid_price, ask_price)
        """
        half_spread = spread / 2
        
        bid_price = fair_value * (1 - half_spread)
        ask_price = fair_value * (1 + half_spread)
        
        # Ensure prices are within valid bounds [0.0001, 0.9999]
        bid_price = max(0.0001, min(0.9999, bid_price))
        ask_price = max(0.0001, min(0.9999, ask_price))
        
        # Ensure bid < ask
        if bid_price >= ask_price:
            mid = (bid_price + ask_price) / 2
            bid_price = mid - 0.0001
            ask_price = mid + 0.0001
        
        return bid_price, ask_price
    
    def get_tick_size(self, token_id: str) -> float:
        """Get minimum tick size for a token"""
        try:
            response = requests.get(f"https://clob.polymarket.com/tick-size?token_id={token_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return float(data.get('minimum_tick_size', 0.0001))
        except:
            pass
        return 0.0001  # Default tick size
    
    def round_to_tick(self, price: float, tick_size: float) -> float:
        """Round price to nearest valid tick"""
        return round(price / tick_size) * tick_size
    
    def create_market_making_orders(self, token_id: str) -> List[Dict[str, Any]]:
        """
        Create a set of market making orders for a token
        
        Args:
            token_id: Token to make markets for
            
        Returns:
            List of order specifications
        """
        orders = []
        
        # Get fair value
        fair_value = self.get_fair_value(token_id)
        if not fair_value:
            logger.warning(f"Cannot determine fair value for {token_id}")
            return orders
        
        # Get tick size
        tick_size = self.get_tick_size(token_id)
        
        # Create multiple price levels
        for level in range(1, self.price_levels + 1):
            # Increase spread for each level
            level_spread = self.spread_target * level
            bid_price, ask_price = self.calculate_quote_prices(fair_value, level_spread)
            
            # Round to tick size
            bid_price = self.round_to_tick(bid_price, tick_size)
            ask_price = self.round_to_tick(ask_price, tick_size)
            
            # Adjust order size (smaller for wider levels)
            level_size = self.order_size / level
            
            # Create bid order
            orders.append({
                'side': BUY,
                'price': bid_price,
                'size': level_size,
                'token_id': token_id,
                'level': level
            })
            
            # Create ask order
            orders.append({
                'side': SELL,
                'price': ask_price,
                'size': level_size,
                'token_id': token_id,
                'level': level
            })
        
        logger.info(f"Created {len(orders)} market making orders for {token_id} around fair value ${fair_value:.4f}")
        return orders
    
    def check_position_limits(self, token_id: str, side: str, size: float) -> bool:
        """
        Check if placing an order would exceed position limits
        
        Args:
            token_id: Token to check
            side: BUY or SELL
            size: Order size
            
        Returns:
            True if order is within limits
        """
        current_position = self.positions.get(token_id, 0.0)
        
        if side == BUY:
            new_position = current_position + size
        else:  # SELL
            new_position = current_position - size
        
        if abs(new_position) > self.max_position:
            logger.warning(f"Position limit exceeded for {token_id}: {new_position} > {self.max_position}")
            return False
        
        return True
    
    def place_order(self, order_spec: Dict[str, Any]) -> Optional[str]:
        """
        Place a single market making order
        
        Args:
            order_spec: Order specification dictionary
            
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            token_id = order_spec['token_id']
            side = order_spec['side']
            price = order_spec['price']
            size = order_spec['size']
            
            # Check position limits
            if not self.check_position_limits(token_id, side, size):
                return None
            
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
            
            # Add negative risk flag if needed
            if is_neg_risk:
                try:
                    order_args.negrisk = True
                except:
                    logger.debug("Client doesn't support negrisk parameter")
            
            # Submit order as GTC (Good-Till-Cancelled)
            response = self.client.create_and_post_order(order_args)
            
            # Extract order ID from response
            order_id = None
            if hasattr(response, 'orderId'):
                order_id = response.orderId
            elif isinstance(response, dict) and 'orderId' in response:
                order_id = response['orderId']
            
            if order_id:
                # Track the order
                self.active_orders[order_id] = {
                    'token_id': token_id,
                    'side': side,
                    'price': price,
                    'size': size,
                    'level': order_spec.get('level', 1),
                    'timestamp': time.time()
                }
                
                logger.info(f"✅ Placed {side} order: {size} @ ${price:.4f} (Order ID: {order_id})")
                return order_id
            else:
                logger.warning(f"Order placed but no order ID returned: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to place order {order_spec}: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an active order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful
        """
        try:
            # Cancel the order
            response = self.client.cancel_order(order_id)
            
            # Remove from tracking
            if order_id in self.active_orders:
                order_info = self.active_orders[order_id]
                logger.info(f"❌ Cancelled {order_info['side']} order: {order_info['size']} @ ${order_info['price']:.4f}")
                del self.active_orders[order_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def cancel_all_orders(self, token_id: Optional[str] = None) -> int:
        """
        Cancel all active orders, optionally filtered by token
        
        Args:
            token_id: If specified, only cancel orders for this token
            
        Returns:
            Number of orders cancelled
        """
        orders_to_cancel = []
        
        for order_id, order_info in self.active_orders.items():
            if token_id is None or order_info['token_id'] == token_id:
                orders_to_cancel.append(order_id)
        
        cancelled_count = 0
        for order_id in orders_to_cancel:
            if self.cancel_order(order_id):
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} orders")
        return cancelled_count
    
    def update_positions(self):
        """Update position tracking based on filled orders"""
        # This would typically query the API for current positions
        # For now, we'll implement a simplified version
        try:
            # Get current positions from API (if available)
            # positions = self.client.get_positions()  # Not implemented in py-clob-client
            
            # For now, we'll track positions based on order fills
            # This is a simplified approach - in production you'd want to query actual positions
            pass
            
        except Exception as e:
            logger.debug(f"Could not update positions: {e}")
    
    def run_market_making_cycle(self, token_ids: List[str]):
        """
        Run one cycle of market making
        
        Args:
            token_ids: List of tokens to make markets for
        """
        logger.info(f"🏭 Starting market making cycle for {len(token_ids)} tokens")
        
        for token_id in token_ids:
            try:
                logger.debug(f"Processing token {token_id}")
                
                # Cancel existing orders for this token
                self.cancel_all_orders(token_id)
                
                # Wait a moment for cancellations to process
                time.sleep(1)
                
                # Create new orders
                orders = self.create_market_making_orders(token_id)
                
                # Place orders with delays to avoid rate limiting
                placed_count = 0
                for order_spec in orders:
                    if self.place_order(order_spec):
                        placed_count += 1
                    
                    # Small delay between orders
                    time.sleep(0.5)
                
                logger.info(f"📊 Token {token_id}: Placed {placed_count}/{len(orders)} orders")
                
                # Delay between tokens
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing token {token_id}: {e}")
                continue
        
        # Update position tracking
        self.update_positions()
        
        logger.info(f"✅ Market making cycle complete. Active orders: {len(self.active_orders)}")

def create_market_maker_config() -> Dict[str, Any]:
    """Create default market maker configuration"""
    return {
        'market_maker': {
            'order_size': 1.0,           # Size per order in USDC
            'spread_target': 0.02,       # Target spread (2%)
            'max_position': 10.0,        # Maximum position per token
            'price_levels': 3,           # Number of price levels to quote
            'refresh_interval': 30,      # Seconds between order refreshes
        }
    }

def run_market_maker(client: ClobClient, token_ids: List[str], config: Dict[str, Any], iterations: Optional[int] = None):
    """
    Run the market making engine
    
    Args:
        client: CLOB client
        token_ids: List of tokens to make markets for
        config: Configuration dictionary
        iterations: Number of cycles to run (None for infinite)
    """
    logger.info("🏭 Starting Market Making Engine")
    
    # Create market maker
    market_maker = MarketMaker(client, config)
    
    iteration = 0
    try:
        while iterations is None or iteration < iterations:
            iteration += 1
            logger.info(f"--- Market Making Cycle {iteration} ---")
            
            # Run market making cycle
            market_maker.run_market_making_cycle(token_ids)
            
            # Wait before next cycle
            refresh_interval = config.get('market_maker', {}).get('refresh_interval', 30)
            logger.info(f"⏰ Waiting {refresh_interval} seconds before next cycle...")
            time.sleep(refresh_interval)
            
    except KeyboardInterrupt:
        logger.info("🛑 Market making stopped by user")
    except Exception as e:
        logger.error(f"Market making error: {e}")
    finally:
        # Clean up - cancel all orders
        logger.info("🧹 Cleaning up - cancelling all orders...")
        market_maker.cancel_all_orders()
        logger.info("✅ Market making engine stopped")

if __name__ == "__main__":
    # This module is designed to be imported and used by the main bot
    # But we can add a simple test here
    print("🏭 Flowbot Market Maker Module")
    print("This module provides liquidity through structured limit orders")
    print("Import this module and use run_market_maker() function") 