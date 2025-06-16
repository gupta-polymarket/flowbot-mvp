#!/usr/bin/env python3
"""
Test Market Maker - Demonstrates market making functionality

This script tests the market maker module with a single token
to validate the price discovery and order placement logic.
"""
import os
import sys
import logging
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from py_clob_client.client import ClobClient

from flowbot.market_maker import MarketMaker, create_market_maker_config
from flowbot.bot import setup_clob_client

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('test_market_maker')

def test_fair_value_calculation():
    """Test fair value calculation for a known token"""
    logger.info("=== Testing Fair Value Calculation ===")
    
    try:
        # Load environment and setup client
        load_dotenv()
        client = setup_clob_client()
        
        # Create market maker with test config
        config = create_market_maker_config()
        market_maker = MarketMaker(client, config)
        
        # Test with first active token from Gamma API
        test_token = "5044658213116494392261893544497225363846217319105609804585534197935770239191"
        
        logger.info(f"Testing fair value calculation for token: {test_token}")
        
        # Get fair value
        fair_value = market_maker.get_fair_value(test_token)
        
        if fair_value:
            logger.info(f"✅ Fair value calculated: ${fair_value:.4f}")
            
            # Test quote price calculation
            spread = 0.02  # 2%
            bid_price, ask_price = market_maker.calculate_quote_prices(fair_value, spread)
            
            logger.info(f"📊 Quote prices with {spread*100}% spread:")
            logger.info(f"   Bid: ${bid_price:.4f}")
            logger.info(f"   Ask: ${ask_price:.4f}")
            logger.info(f"   Spread: ${ask_price - bid_price:.4f} ({((ask_price - bid_price) / fair_value * 100):.2f}%)")
            
            return True
        else:
            logger.error("❌ Failed to calculate fair value")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

def test_order_creation():
    """Test market making order creation"""
    logger.info("=== Testing Order Creation ===")
    
    try:
        # Load environment and setup client
        load_dotenv()
        client = setup_clob_client()
        
        # Create market maker with test config
        config = create_market_maker_config()
        config['market_maker']['order_size'] = 0.50  # Small test size
        config['market_maker']['price_levels'] = 2   # Fewer levels for testing
        
        market_maker = MarketMaker(client, config)
        
        # Test with first active token from Gamma API
        test_token = "5044658213116494392261893544497225363846217319105609804585534197935770239191"
        
        logger.info(f"Creating market making orders for token: {test_token}")
        
        # Create orders
        orders = market_maker.create_market_making_orders(test_token)
        
        if orders:
            logger.info(f"✅ Created {len(orders)} orders:")
            for i, order in enumerate(orders):
                side = "BUY " if order['side'] == 'BUY' else "SELL"
                logger.info(f"   {i+1}. {side} {order['size']:.2f} @ ${order['price']:.4f} (Level {order['level']})")
            
            return True
        else:
            logger.error("❌ No orders created")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

def test_market_maker_dry_run():
    """Test market maker in dry-run mode (no actual orders)"""
    logger.info("=== Testing Market Maker Dry Run ===")
    
    try:
        # Load environment and setup client
        load_dotenv()
        client = setup_clob_client()
        
        # Create market maker with conservative test config
        config = create_market_maker_config()
        config['market_maker']['order_size'] = 0.25      # Very small orders
        config['market_maker']['spread_target'] = 0.05   # Wide spread (5%)
        config['market_maker']['price_levels'] = 2       # Just 2 levels
        config['market_maker']['max_position'] = 2.0     # Low position limit
        
        market_maker = MarketMaker(client, config)
        
        # Test tokens (first active token from Gamma API)
        test_tokens = ["5044658213116494392261893544497225363846217319105609804585534197935770239191"]
        
        logger.info("🧪 Running market maker dry-run cycle...")
        logger.info("Note: This will create order specs but NOT place actual orders")
        
        for token_id in test_tokens:
            logger.info(f"\n--- Processing Token {token_id} ---")
            
            # Get fair value
            fair_value = market_maker.get_fair_value(token_id)
            if not fair_value:
                logger.warning(f"Skipping token {token_id} - no fair value")
                continue
            
            # Create orders (but don't place them)
            orders = market_maker.create_market_making_orders(token_id)
            
            logger.info(f"📋 Would create {len(orders)} orders:")
            total_buy_size = 0
            total_sell_size = 0
            
            for order in orders:
                side_str = "BUY " if order['side'] == 'BUY' else "SELL"
                logger.info(f"   {side_str} {order['size']:.3f} @ ${order['price']:.4f}")
                
                if order['side'] == 'BUY':
                    total_buy_size += order['size']
                else:
                    total_sell_size += order['size']
            
            logger.info(f"📊 Summary:")
            logger.info(f"   Fair Value: ${fair_value:.4f}")
            logger.info(f"   Total Buy Size: {total_buy_size:.3f} USDC")
            logger.info(f"   Total Sell Size: {total_sell_size:.3f} USDC")
            logger.info(f"   Capital at Risk: ~${total_buy_size + total_sell_size:.2f}")
        
        logger.info("✅ Dry-run completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Dry-run test failed: {e}")
        return False

def main():
    """Run all market maker tests"""
    logger.info("🏭 === Market Maker Test Suite ===")
    
    tests = [
        ("Fair Value Calculation", test_fair_value_calculation),
        ("Order Creation", test_order_creation),
        ("Market Maker Dry Run", test_market_maker_dry_run),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Market maker is ready to use.")
        logger.info("\nTo run the market maker:")
        logger.info("  python market_maker_bot.py --dry-run  # Test mode")
        logger.info("  python market_maker_bot.py --token <TOKEN_ID> --cycles 1  # Single cycle")
    else:
        logger.error("⚠️  Some tests failed. Please review the issues above.")

if __name__ == "__main__":
    main() 