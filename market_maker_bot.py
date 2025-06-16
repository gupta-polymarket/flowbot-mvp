#!/usr/bin/env python3
"""
Market Maker Bot - Standalone script for providing liquidity on Polymarket

This bot places structured limit orders to:
- Provide liquidity for price discovery
- Improve bid-ask spreads
- Generate potential profits from market making
"""
import os
import sys
import argparse
import logging
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from py_clob_client.client import ClobClient

from flowbot.market_maker import run_market_maker, create_market_maker_config
from flowbot.bot import get_active_markets_from_gamma, setup_clob_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('market_maker_bot')

def load_market_maker_config() -> Dict[str, Any]:
    """Load market maker configuration"""
    config = create_market_maker_config()
    
    # Override with environment variables if present
    if os.getenv('MM_ORDER_SIZE'):
        config['market_maker']['order_size'] = float(os.getenv('MM_ORDER_SIZE'))
    
    if os.getenv('MM_SPREAD_TARGET'):
        config['market_maker']['spread_target'] = float(os.getenv('MM_SPREAD_TARGET'))
    
    if os.getenv('MM_MAX_POSITION'):
        config['market_maker']['max_position'] = float(os.getenv('MM_MAX_POSITION'))
    
    if os.getenv('MM_PRICE_LEVELS'):
        config['market_maker']['price_levels'] = int(os.getenv('MM_PRICE_LEVELS'))
    
    if os.getenv('MM_REFRESH_INTERVAL'):
        config['market_maker']['refresh_interval'] = int(os.getenv('MM_REFRESH_INTERVAL'))
    
    return config

def main():
    """Main entry point for the Market Maker Bot"""
    parser = argparse.ArgumentParser(description="Flowbot Market Maker - Provides liquidity through limit orders")
    parser.add_argument("--token", type=str, help="Specific token ID to make markets for")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no actual orders)")
    parser.add_argument("--cycles", type=int, help="Number of market making cycles to run (default: infinite)")
    parser.add_argument("--order-size", type=float, help="Order size in USDC (default: 1.0)")
    parser.add_argument("--spread", type=float, help="Target spread as decimal (default: 0.02 for 2%)")
    parser.add_argument("--levels", type=int, help="Number of price levels (default: 3)")
    
    args = parser.parse_args()
    
    logger.info("🏭 === Market Maker Bot Starting ===")
    logger.info(f"Arguments: token={args.token}, dry_run={args.dry_run}, cycles={args.cycles}")
    
    if args.dry_run:
        logger.info("🧪 DRY-RUN MODE: No actual orders will be placed")
        return
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        config = load_market_maker_config()
        
        # Override config with command line arguments
        if args.order_size:
            config['market_maker']['order_size'] = args.order_size
        if args.spread:
            config['market_maker']['spread_target'] = args.spread
        if args.levels:
            config['market_maker']['price_levels'] = args.levels
        
        logger.info(f"Configuration: {config['market_maker']}")
        
        # Get token IDs to make markets for
        if args.token:
            token_ids = [args.token]
            logger.info(f"Making markets for specific token: {args.token}")
        else:
            logger.info("Discovering active markets from Gamma API...")
            token_ids = get_active_markets_from_gamma()
            logger.info(f"Found {len(token_ids)} active tokens")
            
            # Limit to first 10 tokens for manageable market making
            if len(token_ids) > 10:
                token_ids = token_ids[:10]
                logger.info(f"Limited to first 10 tokens for market making")
        
        if not token_ids:
            logger.error("No tokens found for market making")
            return
        
        # Setup CLOB client
        logger.info("Setting up CLOB client...")
        client = setup_clob_client()
        logger.info("CLOB client setup complete")
        
        # Run market maker
        logger.info(f"🚀 Starting market making for {len(token_ids)} tokens")
        run_market_maker(client, token_ids, config, args.cycles)
        
    except KeyboardInterrupt:
        logger.info("🛑 Market maker stopped by user")
    except Exception as e:
        logger.error(f"Market maker error: {e}")
        raise
    finally:
        logger.info("=== Market Maker Bot Stopped ===")

if __name__ == "__main__":
    main() 