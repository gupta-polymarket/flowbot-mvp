#!/usr/bin/env python3
"""
Flowbot - Automated Polymarket liquidity taker bot

This bot randomly takes best bid/ask orders with random quantities to artificially 
tighten spreads using the Polymarket API and PyCLOB client.
"""

import argparse
import logging
import os
import time
import random
import json
from collections import defaultdict
from decimal import Decimal
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType

# Try to import order side constants, but fallback to string names if library signature changes
try:
    from py_clob_client.order_builder.constants import BUY, SELL  # type: ignore
except ImportError:  # pragma: no cover
    BUY, SELL = "BUY", "SELL"

from flowbot.config import load_config
from flowbot.distributions import (
    sample_quantity,
    sample_interval,
    sample_side,
    sample_market,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("flowbot")

POLYGON_CHAIN_ID = 137

# Budget tracking: cumulative USDC spent on BUY orders per token_id for the current run
_spent_usdc: Dict[str, float] = defaultdict(float)


class FlowbotError(Exception):
    """Base exception for Flowbot errors"""
    pass


class MarketResolutionError(FlowbotError):
    """Error resolving market identifiers to token IDs"""
    pass


class OrderExecutionError(FlowbotError):
    """Error executing orders"""
    pass


def validate_token_id(token_id: str) -> bool:
    """Validate that a token ID looks correct (should be a long numeric string)"""
    return token_id.isdigit() and len(token_id) > 50


def get_best_price(orderbook: Dict[str, Any], side: str) -> Optional[float]:
    """
    Get the best price from orderbook for the given side.
    
    Args:
        orderbook: Orderbook data from CLOB API
        side: "BUY" (look at asks) or "SELL" (look at bids)
    
    Returns:
        Best price as float, or None if no liquidity
    """
    try:
        levels = orderbook.get("asks" if side == "BUY" else "bids", [])
        if not levels:
            return None
        
        price_str = levels[0].get("price")
        if price_str is None:
            return None
            
        return float(price_str)
    except (ValueError, TypeError, IndexError) as e:
        logger.error("Error parsing orderbook price: %s", e)
        return None


def resolve_url_to_token_ids(url: str, clob_host: str) -> List[str]:
    """
    Resolve a Polymarket URL to outcome token IDs.
    
    Args:
        url: Full Polymarket URL
        clob_host: CLOB API host
        
    Returns:
        List of token IDs (typically 2: YES and NO)
        
    Raises:
        MarketResolutionError: If resolution fails
    """
    logger.debug("Resolving URL to token IDs: %s", url)
    
    try:
        # Extract slug from URL
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        
        if "event" not in path_parts:
            raise MarketResolutionError(f"URL does not contain '/event/': {url}")
            
        event_idx = path_parts.index("event")
        if event_idx + 1 >= len(path_parts):
            raise MarketResolutionError(f"No slug found after '/event/' in URL: {url}")
            
        slug = path_parts[event_idx + 1]
        logger.debug("Extracted slug: %s", slug)
        
        # Search for market by slug
        search_url = f"{clob_host}/markets?search={slug}"
        logger.debug("Searching markets: %s", search_url)
        
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.debug("Search response type: %s", type(data))
        
        # Handle different response formats
        markets = None
        if isinstance(data, list):
            markets = data
        elif isinstance(data, dict):
            markets = data.get("data") or data.get("markets")
        
        if not markets or not isinstance(markets, list):
            raise MarketResolutionError(f"No markets found in search response for slug: {slug}")
            
        logger.debug("Found %d markets in search results", len(markets))
        
        # Find exact slug match or use first result
        target_market = None
        for market in markets:
            if isinstance(market, dict) and market.get("slug") == slug:
                target_market = market
                break
        
        if not target_market and markets:
            target_market = markets[0]
            logger.debug("Using first search result as no exact slug match found")
            
        if not target_market:
            raise MarketResolutionError(f"No market found for slug: {slug}")
            
        # Extract token IDs from market
        token_ids = extract_token_ids_from_market(target_market)
        logger.info("Resolved URL to %d token IDs: %s", len(token_ids), token_ids)
        
        return token_ids
        
    except requests.RequestException as e:
        raise MarketResolutionError(f"API request failed: {e}") from e
    except Exception as e:
        raise MarketResolutionError(f"Failed to resolve URL {url}: {e}") from e


def extract_token_ids_from_market(market: Dict[str, Any]) -> List[str]:
    """
    Extract outcome token IDs from a market object.
    
    Args:
        market: Market data from CLOB API
        
    Returns:
        List of token IDs
        
    Raises:
        MarketResolutionError: If token IDs cannot be extracted
    """
    logger.debug("Extracting token IDs from market: %s", market.get("slug", "unknown"))
    
    token_ids = []
    
    # Try different field name patterns
    field_patterns = [
        ("yesClobTokenId", "noClobTokenId"),
        ("yes_clob_token_id", "no_clob_token_id"),
        ("yesTokenId", "noTokenId"),
        ("yes_token_id", "no_token_id"),
    ]
    
    for yes_field, no_field in field_patterns:
        yes_token = market.get(yes_field)
        no_token = market.get(no_field)
        
        if yes_token and no_token:
            token_ids = [str(yes_token), str(no_token)]
            logger.debug("Found token IDs using fields %s/%s: %s", yes_field, no_field, token_ids)
            break
    
    # Fallback: look for tokens array
    if not token_ids and "tokens" in market:
        tokens = market["tokens"]
        if isinstance(tokens, list) and len(tokens) >= 2:
            for token in tokens:
                if isinstance(token, dict) and "token_id" in token:
                    token_ids.append(str(token["token_id"]))
            logger.debug("Found token IDs from tokens array: %s", token_ids)
    
    # Validate token IDs
    valid_tokens = [tid for tid in token_ids if validate_token_id(tid)]
    
    if not valid_tokens:
        raise MarketResolutionError(f"No valid token IDs found in market: {market}")
    
    logger.debug("Validated %d token IDs: %s", len(valid_tokens), valid_tokens)
    return valid_tokens


def resolve_market_identifiers(identifiers: List[str]) -> List[str]:
    """
    Resolve various market identifier formats to token IDs.
    
    Args:
        identifiers: List of market identifiers (URLs, market IDs, slugs, or token IDs)
        
    Returns:
        List of resolved token IDs
        
    Raises:
        MarketResolutionError: If resolution fails
    """
    logger.info(f"Resolving {len(identifiers)} market identifiers")
    logger.debug(f"Resolving {len(identifiers)} market identifiers")
    
    resolved_tokens = set()
    
    for identifier in identifiers:
        logger.debug(f"Processing identifier: {identifier}")
        
        # Check if it's already a token ID (long numeric string)
        if identifier.isdigit() and len(identifier) > 50:
            logger.debug(f"Using identifier as token ID: {identifier}")
            resolved_tokens.add(identifier)
            continue
        
        # Check if it's a Polymarket URL
        if "polymarket.com" in identifier:
            logger.debug(f"Detected Polymarket URL: {identifier}")
            tokens = resolve_polymarket_url(identifier)
            resolved_tokens.update(tokens)
            continue
        
        # Try to resolve as market ID or slug using Gamma API
        logger.debug(f"Attempting to resolve via Gamma API: {identifier}")
        tokens = resolve_via_gamma_api(identifier)
        if tokens:
            resolved_tokens.update(tokens)
            continue
        
        # If all else fails, assume it's a token ID
        logger.debug(f"Using identifier as token ID (fallback): {identifier}")
        resolved_tokens.add(identifier)
    
    result = list(resolved_tokens)
    logger.info(f"Resolved to {len(result)} unique token IDs: {result}")
    return result


def resolve_via_gamma_api(identifier: str) -> List[str]:
    """
    Resolve market identifier using Gamma API.
    
    Args:
        identifier: Market ID, slug, or other identifier
        
    Returns:
        List of token IDs for the market
    """
    try:
        gamma_host = "https://gamma-api.polymarket.com"
        
        # Try different query approaches
        queries = [
            f"{gamma_host}/markets?id={identifier}",
            f"{gamma_host}/markets?slug={identifier}",
        ]
        
        for query_url in queries:
            try:
                logger.debug(f"Querying Gamma API: {query_url}")
                response = requests.get(query_url, timeout=10)
                response.raise_for_status()
                markets = response.json()
                
                if markets and isinstance(markets, list) and len(markets) > 0:
                    market = markets[0]
                    
                    # Check if market has orderbook enabled
                    enable_order_book = market.get("enableOrderBook", False)
                    if not enable_order_book:
                        logger.debug(f"Market {identifier} does not have orderbook enabled")
                        continue
                    
                    # Extract token IDs
                    clob_token_ids = market.get("clobTokenIds", [])
                    if clob_token_ids:
                        logger.debug(f"Found {len(clob_token_ids)} token IDs via Gamma API")
                        return [str(tid) for tid in clob_token_ids]
                        
            except Exception as e:
                logger.debug(f"Gamma API query failed for {query_url}: {e}")
                continue
        
        return []
        
    except Exception as e:
        logger.debug(f"Gamma API resolution failed for {identifier}: {e}")
        return []


def get_active_markets_from_gamma() -> List[str]:
    """
    Get active markets with orderbooks enabled from Gamma API.
    
    Returns:
        List of token IDs from active markets
    """
    try:
        gamma_host = "https://gamma-api.polymarket.com"
        
        # Get active markets with orderbooks enabled
        url = f"{gamma_host}/markets?active=true&closed=false&limit=100"
        logger.debug(f"Fetching active markets from: {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        markets = response.json()
        
        active_tokens = []
        for market in markets:
            if isinstance(market, dict):
                enable_order_book = market.get("enableOrderBook", False)
                active = market.get("active", False)
                closed = market.get("closed", True)
                clob_token_ids = market.get("clobTokenIds", [])
                
                if enable_order_book and active and not closed and clob_token_ids:
                    question = market.get("question", "Unknown")
                    
                    # Parse clobTokenIds - it can be a JSON string or a list
                    token_ids = []
                    if isinstance(clob_token_ids, str):
                        try:
                            token_ids = json.loads(clob_token_ids)
                        except json.JSONDecodeError:
                            logger.debug(f"Failed to parse clobTokenIds as JSON: {clob_token_ids}")
                            continue
                    elif isinstance(clob_token_ids, list):
                        token_ids = clob_token_ids
                    
                    # Add valid token IDs
                    for token_id in token_ids:
                        if isinstance(token_id, str) and len(token_id) > 50:  # Valid token ID
                            active_tokens.append(token_id)
                        elif isinstance(token_id, (int, float)):  # Convert numbers to strings
                            active_tokens.append(str(token_id))
                    
                    if token_ids:
                        logger.debug(f"Found active market: {question[:50]}... with {len(token_ids)} tokens")
        
        logger.info(f"Found {len(active_tokens)} token IDs from {len(markets)} active markets")
        return active_tokens
        
    except Exception as e:
        logger.error(f"Failed to fetch active markets from Gamma API: {e}")
        return []


def get_market_info(token_id: str) -> str:
    """Get human-readable market information for a token ID."""
    try:
        gamma_host = "https://gamma-api.polymarket.com"
        response = requests.get(f"{gamma_host}/markets?limit=100&active=true&closed=false", timeout=10)
        response.raise_for_status()
        markets = response.json()
        
        for market in markets:
            if isinstance(market, dict) and market.get("enableOrderBook"):
                clob_token_ids = market.get("clobTokenIds", "")
                if isinstance(clob_token_ids, str):
                    try:
                        token_list = json.loads(clob_token_ids)
                        if token_id in token_list:
                            question = market.get("question", "Unknown market")
                            # Truncate long questions
                            if len(question) > 80:
                                question = question[:77] + "..."
                            return question
                    except (json.JSONDecodeError, TypeError):
                        continue
        return "Unknown market"
    except Exception:
        return "Unknown market"


def execute_trade(client: ClobClient, token_id: str, side: str, quantity: float, 
                 orderbook, config: Dict[str, Any]):
    """
    Execute a trade on the given token.
    
    Args:
        client: CLOB client instance
        token_id: Token ID to trade
        side: "BUY" or "SELL"
        quantity: Quantity in USDC
        orderbook: OrderBookSummary object from CLOB API
        config: Configuration dictionary
    """
    try:
        # Get best price from orderbook
        if side == "BUY":
            asks = orderbook.asks
            if not asks:
                logger.warning(f"No asks available for token {token_id}")
                return
            best_price = float(asks[0].price)
        else:  # SELL
            bids = orderbook.bids
            if not bids:
                logger.warning(f"No bids available for token {token_id}")
                return
            best_price = float(bids[0].price)
        
        # Calculate size in shares
        if side == "BUY":
            size = quantity / best_price  # USDC / price = shares
        else:
            size = quantity  # For SELL, quantity is already in shares
        
        # Get market information
        market_info = get_market_info(token_id)
        
        # Display order details clearly
        print("\n" + "="*80)
        print("🎯 PROPOSED TRADE")
        print("="*80)
        print(f"📊 Market: {market_info}")
        print(f"🪙 Token ID: {token_id}")
        print(f"📈 Action: {side}")
        print(f"💰 Price: ${best_price:.4f} per share")
        print(f"📦 Quantity: {size:.2f} shares")
        print(f"💵 Total Cost: ${quantity:.2f} USDC")
        print(f"📊 Current Spent on this market: ${_spent_usdc.get(token_id, 0):.2f} USDC")
        print("="*80)
        
        # Manual approval if enabled
        if config.get("manual_approval", False):
            while True:
                approval = input("\n🤔 Approve this trade? (y/n/q): ").lower().strip()
                if approval == 'y':
                    print("✅ Trade approved! Executing...")
                    break
                elif approval == 'n':
                    print("❌ Trade rejected. Skipping...")
                    return
                elif approval == 'q':
                    print("🛑 Quitting bot...")
                    exit(0)
                else:
                    print("Please enter 'y' for yes, 'n' for no, or 'q' to quit")
        
        logger.info(f"Best {side} price: {best_price:.4f}")
        logger.info(f"Creating order: {side} {size:.2f} shares @ {best_price:.4f} ({quantity:.4f} USDC)")
        
        # Check if this is a negative risk market
        try:
            neg_risk_response = requests.get(f"https://clob.polymarket.com/neg-risk?token_id={token_id}", timeout=5)
            is_neg_risk = neg_risk_response.status_code == 200 and neg_risk_response.json().get("negRisk", False)
        except:
            is_neg_risk = False
        
        # Create order arguments
        order_args = OrderArgs(
            price=best_price,
            size=size,
            side=BUY if side == "BUY" else SELL,
            token_id=token_id
        )
        
        # Add negative risk flag if needed (some versions of the client support this)
        if is_neg_risk:
            try:
                order_args.negrisk = True
            except:
                logger.debug("Client doesn't support negrisk parameter, continuing without it")
        
        # Create and sign the order first
        signed_order = client.create_order(order_args)
        
        # Post the order as GTC (Good-Till-Cancelled)
        response = client.post_order(signed_order, OrderType.GTC)
        
        success = response.get("success", False)
        if success:
            print(f"🎉 Order executed successfully!")
            
            # Track spending
            if token_id not in _spent_usdc:
                _spent_usdc[token_id] = 0
            _spent_usdc[token_id] += quantity
            
            print(f"💳 Total spent on this market: ${_spent_usdc[token_id]:.2f} USDC")
            logger.info(f"Order result: success={success}, response={response}")
            logger.info(f"Total spent on token {token_id}: {_spent_usdc[token_id]:.2f} USDC")
        else:
            error_msg = response.get("errorMsg", "Unknown error")
            print(f"❌ Order failed: {error_msg}")
            logger.warning(f"Order failed: {error_msg}")
        
    except Exception as e:
        print(f"❌ Trade execution failed: {e}")
        logger.error(f"Failed to execute trade: {e}")
        raise OrderExecutionError(f"Trade execution failed: {e}") from e


def setup_clob_client() -> ClobClient:
    """
    Setup and configure the CLOB client.
    
    Returns:
        Configured ClobClient instance
        
    Raises:
        FlowbotError: If setup fails
    """
    try:
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            raise FlowbotError("PRIVATE_KEY not set in environment")
        
        clob_host = os.getenv("CLOB_API_URL", "https://clob.polymarket.com")
        funding_address = os.getenv("FUNDING_ADDRESS")
        
        logger.debug(f"Host: {clob_host}")
        logger.debug(f"Funding address: {funding_address or 'None (direct EOA)'}")
        
        # Create client
        if funding_address:
            # Using proxy wallet with Email/Magic configuration (signature_type=1)
            # This is the working configuration based on our testing
            client = ClobClient(
                host=clob_host,
                key=private_key,
                chain_id=POLYGON_CHAIN_ID,
                signature_type=1,  # Email/Magic proxy mode
                funder=funding_address
            )
            logger.info("Using Email/Magic proxy mode (signature_type=1)")
        else:
            # Direct EOA
            client = ClobClient(
                host=clob_host,
                key=private_key,
                chain_id=POLYGON_CHAIN_ID
            )
            logger.info("Using Direct EOA mode")
        
        # Set API credentials
        logger.debug("Setting API credentials...")
        client.set_api_creds(client.create_or_derive_api_creds())
        
        return client
        
    except Exception as e:
        raise FlowbotError(f"Failed to setup CLOB client: {e}") from e


def run_trading_loop(client: ClobClient, token_ids: List[str], config: Dict[str, Any], 
                    dry_run: bool, max_iterations: Optional[int]):
    """
    Run the main trading loop.
    
    Args:
        client: CLOB client instance
        token_ids: List of token IDs to trade
        config: Configuration dictionary
        dry_run: Whether to run in dry-run mode
        max_iterations: Maximum number of iterations (None for infinite)
    """
    iteration_count = 0
    
    if dry_run:
        logger.info("DRY RUN MODE - No actual orders will be executed")
    
    while True:
        iteration_count += 1
        
        if max_iterations and iteration_count > max_iterations:
            logger.info(f"Reached maximum iterations ({max_iterations}), stopping")
            break
        
        logger.info(f"--- Iteration {iteration_count} ---")
        
        try:
            if dry_run:
                run_dry_iteration(token_ids, config)
                # Always pause in dry run mode
                sleep_time = sample_interval(config)
                print(f"\n⏰ Next opportunity in {sleep_time:.0f} seconds...")
                print("💤 Waiting for next trading window...")
                logger.info(f"Sleeping for {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
            else:
                # Run the iteration (will search until valid market found)
                run_single_iteration(client, token_ids, config)
                
                # Only pause AFTER a successful trade or max attempts reached
                sleep_time = sample_interval(config)
                print(f"\n⏰ Next trading search in {sleep_time:.0f} seconds...")
                print("💤 Waiting before next search...")
                logger.info(f"Sleeping for {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping...")
            break
        except Exception as e:
            logger.error(f"Error in iteration {iteration_count}: {e}")
            logger.info("Continuing to next iteration...")
            # Brief pause before retry on error
            time.sleep(5)
    
    logger.info("=== Flowbot Stopped ===")
    
    # Print final budget summary
    if _spent_usdc:
        logger.info("=== Final Budget Summary ===")
        total_spent = 0
        for token_id, spent in _spent_usdc.items():
            logger.info(f"Token {token_id}: {spent:.4f} USDC")
            total_spent += spent
        logger.info(f"Total spent: {total_spent:.4f} USDC")


def run_dry_iteration(token_ids: List[str], config: Dict[str, Any]):
    """Run a single dry-run iteration"""
    logger.info("=== Starting new iteration ===")
    
    # Sample parameters
    token_id = random.choice(token_ids)
    side = "BUY" if random.random() < config.get("p_buy", 0.5) else "SELL"
    quantity = sample_quantity(config)
    
    logger.info(f"Sampled: token_id={token_id}, side={side}, quantity={quantity}")
    logger.info("DRY RUN: Would fetch orderbook and execute trade here")
    
    time.sleep(0.1)  # Brief pause for dry run


def run_single_iteration(client: ClobClient, token_ids: List[str], config: Dict[str, Any]):
    """Run a single trading iteration - keep searching until a valid market is found"""
    print("\n" + "🔄 " + "="*78)
    print("🤖 FLOWBOT - SEARCHING FOR TRADING OPPORTUNITY")
    print("="*80)
    
    logger.info("=== Starting new iteration ===")
    
    # Keep searching until we find a valid market
    max_attempts = 50  # Prevent infinite loops
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        # Sample parameters for this attempt
        token_id = random.choice(token_ids)
        side = "BUY" if random.random() < config.get("p_buy", 0.5) else "SELL"
        quantity = sample_quantity(config)
        
        print(f"🎲 Attempt {attempt}: Checking token {token_id[:20]}...")
        logger.info(f"Attempt {attempt}: token_id={token_id}, side={side}, quantity={quantity}")
        
        # Check budget first
        max_spend = config.get("max_spend_per_market", float('inf'))
        spent_so_far = _spent_usdc.get(token_id, 0)
        
        if spent_so_far >= max_spend:
            print(f"💸 Budget limit reached for this market, trying another...")
            logger.debug(f"Budget limit reached for token {token_id}")
            continue
        
        # Adjust quantity if needed
        remaining_budget = max_spend - spent_so_far
        if quantity > remaining_budget:
            quantity = remaining_budget
            print(f"💰 Adjusting trade size to remaining budget: ${quantity:.2f}")
            logger.info(f"Adjusted quantity to {quantity:.4f} USDC (remaining budget)")
        
        try:
            # Fetch orderbook
            print(f"📈 Fetching orderbook data...")
            logger.debug(f"Fetching orderbook for token {token_id}")
            orderbook = client.get_order_book(token_id)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
            
            # Check price filtering (10-90 cents)
            min_price = config.get("min_price", 0.10)  # Default 10 cents
            max_price = config.get("max_price", 0.90)  # Default 90 cents
            
            if side == "BUY":
                if not orderbook.asks:
                    print(f"❌ No asks available, trying another market...")
                    logger.debug(f"No asks available for token {token_id}")
                    continue
                best_price = float(orderbook.asks[0].price)
            else:  # SELL
                if not orderbook.bids:
                    print(f"❌ No bids available, trying another market...")
                    logger.debug(f"No bids available for token {token_id}")
                    continue
                best_price = float(orderbook.bids[0].price)
            
            # Apply price filter
            if best_price < min_price or best_price > max_price:
                print(f"📊 Price ${best_price:.4f} outside range ${min_price:.2f}-${max_price:.2f}, trying another...")
                logger.debug(f"Price {best_price:.4f} outside range {min_price:.2f}-{max_price:.2f}")
                continue
            
            # Found a valid market!
            print(f"✅ Found valid market! Price ${best_price:.4f} is in range ${min_price:.2f}-${max_price:.2f}")
            print(f"🎯 TRADING OPPORTUNITY FOUND (attempt {attempt})")
            
            # Execute trade (this will handle manual approval)
            execute_trade(client, token_id, side, quantity, orderbook, config)
            
            # Trade completed successfully, exit the search loop
            logger.info(f"Trade completed successfully after {attempt} attempts")
            return
            
        except Exception as e:
            print(f"❌ Error with this market: {e}")
            logger.error(f"Error in attempt {attempt}: {e}")
            continue
    
    # If we get here, we couldn't find a valid market after max_attempts
    print(f"⚠️  Could not find a valid market after {max_attempts} attempts")
    print(f"💡 This might mean:")
    print(f"   - Most markets are outside the price range (${config.get('min_price', 0.10):.2f}-${config.get('max_price', 0.90):.2f})")
    print(f"   - Budget limits reached on many markets")
    print(f"   - Low liquidity period")
    logger.warning(f"No valid market found after {max_attempts} attempts")


def resolve_polymarket_url(url: str) -> List[str]:
    """
    Resolve a Polymarket URL to token IDs.
    
    Args:
        url: Polymarket URL
        
    Returns:
        List of token IDs for the market
    """
    try:
        # Extract the slug from the URL
        # URL format: https://polymarket.com/event/market-slug?tid=...
        if "/event/" in url:
            # Extract slug between /event/ and ?
            slug_part = url.split("/event/")[1]
            if "?" in slug_part:
                slug = slug_part.split("?")[0]
            else:
                slug = slug_part
            
            logger.debug(f"Extracted slug from URL: {slug}")
            
            # Try to find this market in Gamma API
            gamma_host = "https://gamma-api.polymarket.com"
            
            # Search for markets containing this slug
            search_url = f"{gamma_host}/markets?limit=100"
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            markets = response.json()
            
            # Look for a market that matches the slug
            for market in markets:
                if isinstance(market, dict):
                    market_slug = market.get("slug", "")
                    if slug in market_slug or market_slug in slug:
                        enable_order_book = market.get("enableOrderBook", False)
                        if enable_order_book:
                            clob_token_ids = market.get("clobTokenIds", [])
                            
                            # Parse token IDs
                            token_ids = []
                            if isinstance(clob_token_ids, str):
                                try:
                                    token_ids = json.loads(clob_token_ids)
                                except json.JSONDecodeError:
                                    continue
                            elif isinstance(clob_token_ids, list):
                                token_ids = clob_token_ids
                            
                            if token_ids:
                                question = market.get("question", "Unknown")
                                logger.debug(f"Found matching market: {question}")
                                return [str(tid) for tid in token_ids if tid]
        
        logger.debug(f"Could not resolve Polymarket URL: {url}")
        return []
        
    except Exception as e:
        logger.debug(f"Failed to resolve Polymarket URL {url}: {e}")
        return []


def main():
    """Main entry point for the Flowbot"""
    parser = argparse.ArgumentParser(description="Flowbot - Automated Polymarket Trading Bot")
    parser.add_argument("--market", type=str, help="Specific market identifier to trade")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no actual trades)")
    parser.add_argument("--iterations", type=int, help="Number of iterations to run (default: infinite)")
    
    args = parser.parse_args()
    
    logger.info("=== Flowbot Starting ===")
    logger.info(f"Arguments: market={args.market}, dry_run={args.dry_run}, iterations={args.iterations}")
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Loaded configuration: {config}")
        
        # Handle market specification
        if args.market:
            # Use specific market from command line
            logger.info(f"Using specific market from command line: {args.market}")
            token_ids = resolve_market_identifiers([args.market])
        elif config.get("markets"):
            # Use markets from config
            logger.info(f"Using markets from config: {config['markets']}")
            token_ids = resolve_market_identifiers(config["markets"])
        else:
            # Get active markets from Gamma API
            logger.info("No markets specified, fetching active markets from Gamma API...")
            token_ids = get_active_markets_from_gamma()
            if not token_ids:
                raise FlowbotError("No active markets found from Gamma API")
        
        if not token_ids:
            raise FlowbotError("No valid token IDs resolved")
        
        logger.info(f"Trading on {len(token_ids)} token IDs")
        
        # Setup CLOB client (only if not in dry-run mode)
        if args.dry_run:
            logger.info("DRY RUN MODE - Skipping CLOB client setup")
            client = None
        else:
            logger.info("Setting up CLOB client...")
            client = setup_clob_client()
            logger.info("CLOB client setup complete")
        
        # Start main loop
        logger.info("Starting main loop...")
        run_trading_loop(client, token_ids, config, args.dry_run, args.iterations)
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    exit(main()) 