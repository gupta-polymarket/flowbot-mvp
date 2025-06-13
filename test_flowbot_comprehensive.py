#!/usr/bin/env python3
"""
Comprehensive test suite for Flowbot components
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowbot.config import load_config
from flowbot.distributions import sample_quantity, sample_interval, sample_side, sample_market
from flowbot.bot import (
    validate_token_id,
    get_best_price,
    resolve_url_to_token_ids,
    extract_token_ids_from_market,
    resolve_market_identifiers,
    resolve_market_id_to_token_ids,
    resolve_slug_to_token_ids,
    execute_order,
    setup_client,
    FlowbotError,
    MarketResolutionError,
    OrderExecutionError,
)


class TestTokenValidation(unittest.TestCase):
    def test_validate_token_id_valid(self):
        """Test valid token ID validation"""
        valid_token = "1234567890123456789012345678901234567890123456789012345678901234567890"
        self.assertTrue(validate_token_id(valid_token))
    
    def test_validate_token_id_too_short(self):
        """Test token ID that's too short"""
        short_token = "123456789"
        self.assertFalse(validate_token_id(short_token))
    
    def test_validate_token_id_non_numeric(self):
        """Test non-numeric token ID"""
        non_numeric = "abcd1234567890123456789012345678901234567890123456789012345678901234567890"
        self.assertFalse(validate_token_id(non_numeric))


class TestOrderbookParsing(unittest.TestCase):
    def test_get_best_price_buy_side(self):
        """Test getting best price for BUY side (looks at asks)"""
        orderbook = {
            "asks": [{"price": "0.4500"}, {"price": "0.4600"}],
            "bids": [{"price": "0.4400"}, {"price": "0.4300"}]
        }
        
        price = get_best_price(orderbook, "BUY")
        self.assertEqual(price, 0.45)
    
    def test_get_best_price_sell_side(self):
        """Test getting best price for SELL side (looks at bids)"""
        orderbook = {
            "asks": [{"price": "0.4500"}, {"price": "0.4600"}],
            "bids": [{"price": "0.4400"}, {"price": "0.4300"}]
        }
        
        price = get_best_price(orderbook, "SELL")
        self.assertEqual(price, 0.44)
    
    def test_get_best_price_empty_side(self):
        """Test getting price when one side is empty"""
        orderbook = {"asks": [], "bids": [{"price": "0.4400"}]}
        
        self.assertIsNone(get_best_price(orderbook, "BUY"))
        self.assertEqual(get_best_price(orderbook, "SELL"), 0.44)
    
    def test_get_best_price_malformed_data(self):
        """Test handling malformed orderbook data"""
        malformed_orderbook = {"asks": [{"price": None}], "bids": []}
        
        self.assertIsNone(get_best_price(malformed_orderbook, "BUY"))
    
    def test_get_best_price_missing_keys(self):
        """Test handling missing orderbook keys"""
        incomplete_orderbook = {"asks": [{"not_price": "0.45"}]}
        
        self.assertIsNone(get_best_price(incomplete_orderbook, "BUY"))


class TestMarketResolution(unittest.TestCase):
    def test_extract_token_ids_from_market_clob_fields(self):
        """Test extracting token IDs using CLOB field names"""
        market = {
            "slug": "test-market",
            "yesClobTokenId": "1234567890123456789012345678901234567890123456789012345678901234567890",
            "noClobTokenId": "0987654321098765432109876543210987654321098765432109876543210987654321"
        }
        
        token_ids = extract_token_ids_from_market(market)
        self.assertEqual(len(token_ids), 2)
        self.assertIn("1234567890123456789012345678901234567890123456789012345678901234567890", token_ids)
        self.assertIn("0987654321098765432109876543210987654321098765432109876543210987654321", token_ids)
    
    def test_extract_token_ids_from_market_fallback_fields(self):
        """Test extracting token IDs using fallback field names"""
        market = {
            "slug": "test-market",
            "yesTokenId": "1234567890123456789012345678901234567890123456789012345678901234567890",
            "noTokenId": "0987654321098765432109876543210987654321098765432109876543210987654321"
        }
        
        token_ids = extract_token_ids_from_market(market)
        self.assertEqual(len(token_ids), 2)
    
    def test_extract_token_ids_from_market_tokens_array(self):
        """Test extracting token IDs from tokens array"""
        market = {
            "slug": "test-market",
            "tokens": [
                {"token_id": "1234567890123456789012345678901234567890123456789012345678901234567890"},
                {"token_id": "0987654321098765432109876543210987654321098765432109876543210987654321"}
            ]
        }
        
        token_ids = extract_token_ids_from_market(market)
        self.assertEqual(len(token_ids), 2)
    
    def test_extract_token_ids_from_market_no_valid_tokens(self):
        """Test handling market with no valid token IDs"""
        market = {"slug": "test-market", "invalid_field": "value"}
        
        with self.assertRaises(MarketResolutionError):
            extract_token_ids_from_market(market)
    
    @patch('requests.get')
    def test_resolve_url_to_token_ids_success(self, mock_get):
        """Test successful URL to token ID resolution"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{
                "slug": "test-market-slug",
                "yesClobTokenId": "1234567890123456789012345678901234567890123456789012345678901234567890",
                "noClobTokenId": "0987654321098765432109876543210987654321098765432109876543210987654321"
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        url = "https://polymarket.com/event/test-market-slug?tid=123"
        token_ids = resolve_url_to_token_ids(url, "https://test.com")
        
        self.assertEqual(len(token_ids), 2)
        mock_get.assert_called_once_with("https://test.com/markets?search=test-market-slug", timeout=10)
    
    @patch('requests.get')
    def test_resolve_url_to_token_ids_no_event(self, mock_get):
        """Test URL resolution with invalid URL format"""
        url = "https://polymarket.com/invalid/path"
        
        with self.assertRaises(MarketResolutionError):
            resolve_url_to_token_ids(url, "https://test.com")
    
    @patch('requests.get')
    def test_resolve_url_to_token_ids_api_error(self, mock_get):
        """Test URL resolution with API error"""
        mock_get.side_effect = Exception("API Error")
        
        url = "https://polymarket.com/event/test-slug"
        
        with self.assertRaises(MarketResolutionError):
            resolve_url_to_token_ids(url, "https://test.com")
    
    @patch('requests.get')
    def test_resolve_market_id_to_token_ids_success(self, mock_get):
        """Test successful market ID to token ID resolution"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{
                "marketId": "12345",
                "yesClobTokenId": "1234567890123456789012345678901234567890123456789012345678901234567890",
                "noClobTokenId": "0987654321098765432109876543210987654321098765432109876543210987654321"
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        token_ids = resolve_market_id_to_token_ids("12345", "https://test.com")
        
        self.assertEqual(len(token_ids), 2)
        mock_get.assert_called_once_with("https://test.com/markets", timeout=10)
    
    @patch('requests.get')
    def test_resolve_market_id_to_token_ids_not_found(self, mock_get):
        """Test market ID resolution when market not found"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with self.assertRaises(MarketResolutionError):
            resolve_market_id_to_token_ids("99999", "https://test.com")
    
    @patch('requests.get')
    def test_resolve_slug_to_token_ids_success(self, mock_get):
        """Test successful slug to token ID resolution"""
        mock_response = Mock()
        mock_response.json.return_value = [{
            "slug": "test-slug",
            "yesClobTokenId": "1234567890123456789012345678901234567890123456789012345678901234567890",
            "noClobTokenId": "0987654321098765432109876543210987654321098765432109876543210987654321"
        }]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        token_ids = resolve_slug_to_token_ids("test-slug", "https://test.com")
        
        self.assertEqual(len(token_ids), 2)
    
    @patch('flowbot.bot.resolve_url_to_token_ids')
    @patch('flowbot.bot.resolve_market_id_to_token_ids')
    @patch('flowbot.bot.resolve_slug_to_token_ids')
    def test_resolve_market_identifiers_mixed(self, mock_slug, mock_market_id, mock_url):
        """Test resolving mixed types of market identifiers"""
        # Setup mocks
        mock_url.return_value = ["token1", "token2"]
        mock_market_id.return_value = ["token3", "token4"]
        mock_slug.return_value = ["token5", "token6"]
        
        identifiers = [
            "https://polymarket.com/event/test",
            "12345",  # market ID
            "test-slug",  # slug
            "1234567890123456789012345678901234567890123456789012345678901234567890"  # token ID
        ]
        
        result = resolve_market_identifiers(identifiers, "https://test.com")
        
        # Should have 7 unique tokens (6 from mocks + 1 direct token ID)
        self.assertEqual(len(result), 7)
        self.assertIn("1234567890123456789012345678901234567890123456789012345678901234567890", result)
    
    def test_resolve_market_identifiers_deduplication(self):
        """Test that duplicate token IDs are removed"""
        token_id = "1234567890123456789012345678901234567890123456789012345678901234567890"
        identifiers = [token_id, token_id, token_id]
        
        result = resolve_market_identifiers(identifiers, "https://test.com")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], token_id)


class TestOrderExecution(unittest.TestCase):
    def test_execute_order_success(self):
        """Test successful order execution"""
        mock_client = Mock()
        mock_client.create_order.return_value = "signed_order"
        mock_client.post_order.return_value = {"success": True, "orderId": "12345"}
        
        response = execute_order(mock_client, "token123", "BUY", 0.45, 10.0)
        
        self.assertTrue(response["success"])
        mock_client.create_order.assert_called_once()
        mock_client.post_order.assert_called_once()
    
    def test_execute_order_failure(self):
        """Test order execution failure"""
        mock_client = Mock()
        mock_client.create_order.side_effect = Exception("Order creation failed")
        
        with self.assertRaises(OrderExecutionError):
            execute_order(mock_client, "token123", "BUY", 0.45, 10.0)


class TestClientSetup(unittest.TestCase):
    @patch('flowbot.bot.ClobClient')
    def test_setup_client_direct_eoa(self, mock_clob_client):
        """Test client setup for direct EOA"""
        mock_client_instance = Mock()
        mock_clob_client.return_value = mock_client_instance
        
        client = setup_client("0x123", "https://test.com")
        
        mock_clob_client.assert_called_once_with(
            host="https://test.com",
            key="0x123",
            chain_id=137
        )
        mock_client_instance.set_api_creds.assert_called_once()
    
    @patch('flowbot.bot.ClobClient')
    def test_setup_client_proxy_account(self, mock_clob_client):
        """Test client setup for proxy account"""
        mock_client_instance = Mock()
        mock_clob_client.return_value = mock_client_instance
        
        client = setup_client("0x123", "https://test.com", "0xfunder")
        
        mock_clob_client.assert_called_once_with(
            host="https://test.com",
            key="0x123",
            chain_id=137,
            signature_type=1,
            funder="0xfunder"
        )
    
    @patch('flowbot.bot.ClobClient')
    def test_setup_client_failure(self, mock_clob_client):
        """Test client setup failure"""
        mock_clob_client.side_effect = Exception("Client setup failed")
        
        with self.assertRaises(FlowbotError):
            setup_client("0x123", "https://test.com")


class TestDistributions(unittest.TestCase):
    def test_sample_quantity_uniform(self):
        """Test quantity sampling with uniform distribution"""
        config = {"quantity": {"type": "uniform", "min": 1.0, "max": 25.0}}
        
        for _ in range(10):
            qty = sample_quantity(config)
            self.assertGreaterEqual(qty, 1.0)
            self.assertLessEqual(qty, 25.0)
            # Check that quantity has at most 2 decimal places
            decimal_part = str(qty).split('.')[-1] if '.' in str(qty) else ""
            self.assertLessEqual(len(decimal_part), 2)
    
    def test_sample_interval_uniform(self):
        """Test interval sampling with uniform distribution"""
        config = {"interval": {"type": "uniform", "min": 3, "max": 10}}
        
        for _ in range(10):
            interval = sample_interval(config)
            self.assertGreaterEqual(interval, 3)
            self.assertLessEqual(interval, 10)
    
    def test_sample_side_probability(self):
        """Test side sampling respects probability"""
        config = {"p_buy": 0.0}  # Never buy
        
        for _ in range(10):
            side = sample_side(config)
            self.assertEqual(side, "SELL")
        
        config = {"p_buy": 1.0}  # Always buy
        
        for _ in range(10):
            side = sample_side(config)
            self.assertEqual(side, "BUY")
    
    def test_sample_market_forced(self):
        """Test market sampling with forced market"""
        config = {"markets": ["token1", "token2", "token3"]}
        
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
        
        # With enough samples, all markets should be selected
        self.assertEqual(len(set(markets)), 3)
    
    def test_sample_market_no_markets(self):
        """Test market sampling with no markets configured"""
        config = {}
        
        with self.assertRaises(ValueError):
            sample_market(config)


class TestConfig(unittest.TestCase):
    def test_load_default_config(self):
        """Test loading default configuration"""
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
    
    @patch.dict(os.environ, {"TOKEN_IDS": "token1,token2,token3"})
    def test_load_config_with_env_tokens(self):
        """Test loading config with TOKEN_IDS from environment"""
        with patch('pathlib.Path.exists', return_value=False):
            config = load_config("nonexistent.yaml")
            
            self.assertEqual(config["markets"], ["token1", "token2", "token3"])
    
    @patch.dict(os.environ, {"MARKET_IDS": "123,456,789"})
    def test_load_config_with_env_market_ids(self):
        """Test loading config with MARKET_IDS from environment"""
        with patch('pathlib.Path.exists', return_value=False):
            config = load_config("nonexistent.yaml")
            
            self.assertEqual(config["market_ids"], ["123", "456", "789"])


class TestIntegration(unittest.TestCase):
    """Integration tests that test multiple components together"""
    
    @patch('flowbot.bot.setup_client')
    @patch('flowbot.bot.resolve_market_identifiers')
    @patch('flowbot.bot.load_dotenv')
    @patch('flowbot.bot.load_config')
    @patch.dict(os.environ, {"PRIVATE_KEY": "0x123", "CLOB_API_URL": "https://test.com"})
    def test_main_dry_run(self, mock_load_config, mock_load_dotenv, mock_resolve, mock_setup_client):
        """Test main function in dry run mode"""
        # Setup mocks
        mock_load_config.return_value = {
            "markets": ["https://polymarket.com/event/test"],
            "quantity": {"type": "uniform", "min": 1.0, "max": 10.0},
            "interval": {"type": "uniform", "min": 1, "max": 2},
            "p_buy": 0.5,
            "max_spend_per_market": 5.0
        }
        mock_resolve.return_value = ["1234567890123456789012345678901234567890123456789012345678901234567890"]
        
        from flowbot.bot import main
        
        # Test dry run with limited iterations
        with patch('sys.argv', ['flowbot', '--dry-run', '--iterations', '1']):
            result = main()
            
        self.assertEqual(result, 0)
        mock_setup_client.assert_not_called()  # Should not setup client in dry run


if __name__ == "__main__":
    # Run tests with high verbosity
    unittest.main(verbosity=2) 