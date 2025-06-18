"""
Flowbot - Automated Polymarket Trading Bot

A comprehensive trading bot for Polymarket that includes:
- Random liquidity taking (main bot)
- Market making strategies  
- Spread tightening (taker bot)
"""

__version__ = "1.0.0"

# Import main modules for easy access
from .bot import FlowbotError, MarketResolutionError, OrderExecutionError
from .config import load_config
from .market_maker import MarketMaker, run_market_maker
from .taker_bot import SpreadTighteningBot, resolve_market_urls_to_tokens

__all__ = [
    "FlowbotError",
    "MarketResolutionError", 
    "OrderExecutionError",
    "load_config",
    "MarketMaker",
    "run_market_maker",
    "SpreadTighteningBot",
    "resolve_market_urls_to_tokens"
] 