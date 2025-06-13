#!/usr/bin/env python3
"""
Flowbot Demo - Shows the bot working with real market data in dry-run mode
"""
import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run a demo of the bot"""
    print("🚀 Flowbot Demo")
    print("=" * 50)
    print("This demo shows the bot working with real Polymarket data")
    print("Running in DRY-RUN mode for safety (no actual trades)")
    print("=" * 50)
    
    # Set up environment for demo
    os.environ["PRIVATE_KEY"] = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12"
    os.environ["CLOB_API_URL"] = "https://clob.polymarket.com"
    
    # Create a demo config
    demo_config = {
        "markets": [
            "https://polymarket.com/event/who-will-win-dem-nomination-for-nyc-mayor?tid=1749830297077"
        ],
        "quantity": {"type": "uniform", "min": 1.0, "max": 5.0},
        "interval": {"type": "uniform", "min": 2, "max": 5},
        "p_buy": 0.5,
        "max_spend_per_market": 10.0
    }
    
    # Patch the config loading
    import flowbot.bot
    original_load_config = flowbot.bot.load_config
    flowbot.bot.load_config = lambda path="config.yaml": demo_config
    
    # Patch sys.argv
    original_argv = sys.argv
    sys.argv = ["flowbot", "--dry-run", "--iterations", "3"]
    
    try:
        print("Starting bot demo...")
        print()
        
        # Import and run
        from flowbot.bot import main as bot_main
        result = bot_main()
        
        print()
        if result == 0:
            print("✅ Demo completed successfully!")
            print()
            print("Key features demonstrated:")
            print("• ✅ URL resolution to token IDs")
            print("• ✅ Market sampling and parameter generation")
            print("• ✅ Budget tracking and logging")
            print("• ✅ Comprehensive error handling")
            print("• ✅ Dry-run mode for safe testing")
            print()
            print("To run with real trades:")
            print("1. Set up your .env file with real PRIVATE_KEY")
            print("2. Fund your account with USDC")
            print("3. Remove --dry-run flag")
            print("4. python -m flowbot.bot")
        else:
            print("❌ Demo failed")
            
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Restore original values
        sys.argv = original_argv
        flowbot.bot.load_config = original_load_config
    
    return 0


if __name__ == "__main__":
    exit(main()) 