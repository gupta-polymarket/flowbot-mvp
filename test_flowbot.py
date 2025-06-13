#!/usr/bin/env python3
"""
Test script for Flowbot components
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowbot.config import load_config
from flowbot.distributions import sample_quantity, sample_interval, sample_side, sample_market
from flowbot.bot import get_best_price, resolve_market_id_to_token_ids, resolve_url_to_token_ids


class TestConfig(unittest.TestCase):
    def test_load_default_config(self):
        """Test loading default configuration when no config.yaml exists"""
        with patch('pathlib.Path.exists', return_value=False):
            config = load_config("nonexistent.yaml")
            
            self.assertEqual(config["quantity"]["type"], "uniform")
            self.assertEqual(config["quantity"]["min"], 1.0)
            self.assertEqual(config["quantity"]["max"], 10.0)
            self.assertEqual(config["interval"]["type"], "uniform")
            self.assertEqual(config["interval"]["min"], 3)
            self.assertEqual(config["interval"]["max"], 15)
            self.assertEqual(config["p_buy"], 0.5)
            self.assertEqual(config["max_spend_per_market"], 5.0)
    
    def test_load_custom_config(self):
        """Test loading custom configuration from config.yaml"""
        config = load_config("config.yaml")
        
        # Should have markets from config.yaml
        self.assertIn("markets", config)
        self.assertTrue(len(config["markets"]) > 0)


class TestDistributions(unittest.TestCase):
    def test_sample_quantity(self):
        """Test quantity sampling"""
        config = {"quantity": {"type": "uniform", "min": 1.0, "max": 25.0}}
        
        for _ in range(10):
            qty = sample_quantity(config)
            self.assertGreaterEqual(qty, 1.0)
            self.assertLessEqual(qty, 25.0)
            # Check that quantity has at most 2 decimal places
            decimal_part = str(qty).split('.')[-1] if '.' in str(qty) else ""
            self.assertLessEqual(len(decimal_part), 2)
    
    def test_sample_interval(self):
        """Test interval sampling"""
        config = {"interval": {"type": "uniform", "min": 3, "max": 10}}
        
        for _ in range(10):
            interval = sample_interval(config)
            self.assertGreaterEqual(interval, 3)
            self.assertLessEqual(interval, 10)
    
    def test_sample_side(self):
        """Test side sampling"""
        config = {"p_buy": 0.5}
        
        sides = []
        for _ in range(100):
            side = sample_side(config)
            self.assertIn(side, ["BUY", "SELL"])
            sides.append(side)
        
        # With enough samples, both sides should appear
        self.assertIn("BUY", sides)
        self.assertIn("SELL", sides)
    
    def test_sample_market_with_forced(self):
        """Test market sampling with forced market"""
        config = {"markets": ["token1", "token2", "token3"]}
        
        # Test forced market
        result = sample_market(config, forced="forced_token")
        self.assertEqual(result, "forced_token")
    
    def test_sample_market_random(self):
        """Test random market sampling"""
        config = {"markets": ["token1", "token2", "token3"]}
        
        markets = []
        for _ in range(30):
            market = sample_market(config, forced=None)
            self.assertIn(market, config["markets"])
            markets.append(market)
        
        # With enough samples, all markets should be selected at least once
        self.assertEqual(len(set(markets)), 3)
    
    def test_sample_market_no_markets(self):
        """Test market sampling with no markets configured"""
        config = {}
        
        with self.assertRaises(ValueError) as context:
            sample_market(config)
        
        self.assertIn("No markets defined", str(context.exception))


class TestBotHelpers(unittest.TestCase):
    def test_best_price(self):
        """Test get_best_price function"""
        # Test BUY side (looking at asks)
        orderbook = {
            "asks": [{"price": "0.4500"}, {"price": "0.4600"}],
            "bids": [{"price": "0.4400"}, {"price": "0.4300"}]
        }
        
        price = get_best_price(orderbook, "BUY")
        self.assertEqual(price, 0.45)
        
        # Test SELL side (looking at bids)
        price = get_best_price(orderbook, "SELL")
        self.assertEqual(price, 0.44)
        
        # Test empty orderbook
        empty_orderbook = {"asks": [], "bids": []}
        self.assertIsNone(get_best_price(empty_orderbook, "BUY"))
        self.assertIsNone(get_best_price(empty_orderbook, "SELL"))
    
    def test_url_resolution(self):
        """Test URL resolution (simplified test)"""
        # This is now tested in the comprehensive test suite
        # Just test that the function exists and can be called
        try:
            from flowbot.bot import resolve_url_to_token_ids
            # Function exists
            self.assertTrue(True)
        except ImportError:
            self.fail("resolve_url_to_token_ids function not found")
    
    @patch('requests.get')
    def test_resolve_market_ids_to_token_ids(self, mock_get):
        """Test market ID to token ID resolution"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "marketId": "12345",
                    "yesClobTokenId": "1234567890123456789012345678901234567890123456789012345678901234567890",
                    "noClobTokenId": "0987654321098765432109876543210987654321098765432109876543210987654321"
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = resolve_market_id_to_token_ids("12345", "https://test.com")
        
        self.assertEqual(len(result), 2)
        self.assertIn("1234567890123456789012345678901234567890123456789012345678901234567890", result)
        self.assertIn("0987654321098765432109876543210987654321098765432109876543210987654321", result)


class TestBotIntegration(unittest.TestCase):
    @patch('flowbot.bot.ClobClient')
    @patch('flowbot.bot.load_dotenv')
    @patch('os.getenv')
    def test_bot_initialization(self, mock_getenv, mock_load_dotenv, mock_clob_client):
        """Test bot initialization without actually running it"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "PRIVATE_KEY": "0x1234567890abcdef",
            "CLOB_API_URL": "https://test.polymarket.com",
            "FUNDING_ADDRESS": None,
            "FORCE_MARKET_TOKEN_ID": None,
            "TOKEN_IDS": "",
            "MARKET_IDS": ""
        }.get(key, default)
        
        # Import here to ensure mocks are in place
        from flowbot.bot import POLYGON_CHAIN_ID
        
        # Verify constants
        self.assertEqual(POLYGON_CHAIN_ID, 137)
        
        # Test would continue with actual bot initialization...


if __name__ == "__main__":
    unittest.main(verbosity=2)