#!/usr/bin/env python3
"""
Integration test for Flowbot with real API calls
"""
import os
import sys
import time
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowbot.bot import (
    resolve_url_to_token_ids,
    resolve_market_identifiers,
    validate_token_id,
    logger
)

# Set up logging for integration test
logging.basicConfig(level=logging.INFO)

def test_real_market_resolution():
    """Test market resolution with real Polymarket URLs"""
    print("=== Testing Real Market Resolution ===")
    
    # Test URLs from different markets
    test_urls = [
        "https://polymarket.com/event/who-will-win-dem-nomination-for-nyc-mayor?tid=1749830297077",
        "https://polymarket.com/event/will-tesla-launch-a-driverless-robtotaxi-service-before-july?tid=1749826944603"
    ]
    
    clob_host = "https://clob.polymarket.com"
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            token_ids = resolve_url_to_token_ids(url, clob_host)
            print(f"✅ Resolved to {len(token_ids)} token IDs:")
            for i, token_id in enumerate(token_ids):
                is_valid = validate_token_id(token_id)
                print(f"  {i+1}. {token_id} (valid: {is_valid})")
                
            if not all(validate_token_id(tid) for tid in token_ids):
                print("❌ Some token IDs are invalid!")
                return False
                
        except Exception as e:
            print(f"❌ Failed to resolve URL: {e}")
            return False
    
    print("\n✅ All URL resolutions successful!")
    return True


def test_mixed_identifiers():
    """Test resolving mixed types of identifiers"""
    print("\n=== Testing Mixed Identifier Resolution ===")
    
    # Mix of URLs, potential market IDs, and token IDs
    identifiers = [
        "https://polymarket.com/event/who-will-win-dem-nomination-for-nyc-mayor?tid=1749830297077",
        # Add a real token ID if we have one from the URL resolution
    ]
    
    clob_host = "https://clob.polymarket.com"
    
    try:
        resolved_tokens = resolve_market_identifiers(identifiers, clob_host)
        print(f"✅ Resolved {len(identifiers)} identifiers to {len(resolved_tokens)} token IDs:")
        
        for i, token_id in enumerate(resolved_tokens):
            is_valid = validate_token_id(token_id)
            print(f"  {i+1}. {token_id} (valid: {is_valid})")
            
        if not all(validate_token_id(tid) for tid in resolved_tokens):
            print("❌ Some resolved token IDs are invalid!")
            return False
            
        print("✅ Mixed identifier resolution successful!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to resolve mixed identifiers: {e}")
        return False


def test_bot_dry_run():
    """Test the bot in dry-run mode with real configuration"""
    print("\n=== Testing Bot Dry Run ===")
    
    # Create a temporary config for testing
    test_config = {
        "markets": ["https://polymarket.com/event/who-will-win-dem-nomination-for-nyc-mayor?tid=1749830297077"],
        "quantity": {"type": "uniform", "min": 1.0, "max": 5.0},
        "interval": {"type": "uniform", "min": 1, "max": 3},
        "p_buy": 0.5,
        "max_spend_per_market": 5.0
    }
    
    # Save current config and create test config
    import yaml
    with open("config_test.yaml", "w") as f:
        yaml.dump(test_config, f)
    
    try:
        # Set environment variables for test
        os.environ["PRIVATE_KEY"] = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12"
        os.environ["CLOB_API_URL"] = "https://clob.polymarket.com"
        
        # Import and run main function
        from flowbot.bot import main
        import sys
        
        # Mock sys.argv for the test
        original_argv = sys.argv
        sys.argv = ["flowbot", "--dry-run", "--iterations", "2"]
        
        # Patch config loading to use our test config
        from flowbot.config import load_config
        original_load_config = load_config
        
        def mock_load_config(path="config.yaml"):
            return test_config
        
        # Monkey patch
        import flowbot.bot
        flowbot.bot.load_config = mock_load_config
        
        print("Running bot in dry-run mode...")
        result = main()
        
        # Restore
        sys.argv = original_argv
        flowbot.bot.load_config = original_load_config
        
        if result == 0:
            print("✅ Bot dry run completed successfully!")
            return True
        else:
            print(f"❌ Bot dry run failed with exit code {result}")
            return False
            
    except Exception as e:
        print(f"❌ Bot dry run failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test config
        if os.path.exists("config_test.yaml"):
            os.remove("config_test.yaml")


def main():
    """Run all integration tests"""
    print("🚀 Starting Flowbot Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Real Market Resolution", test_real_market_resolution),
        ("Mixed Identifiers", test_mixed_identifiers),
        ("Bot Dry Run", test_bot_dry_run),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"🏁 Integration Tests Complete: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("💥 Some integration tests failed!")
        return 1


if __name__ == "__main__":
    exit(main()) 