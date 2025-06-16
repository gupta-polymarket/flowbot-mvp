#!/usr/bin/env python3
"""
Setup script to configure Flowbot with Coinbase wallet
"""

import os
import getpass
from pathlib import Path

def main():
    print("🔧 Flowbot Coinbase Wallet Setup")
    print("=" * 50)
    print()
    print("This script will help you configure Flowbot to use your Coinbase wallet.")
    print("Your Coinbase wallet address: 0xdBe52861b497b6D83f4757DB89ECC028896eccA4")
    print()
    print("⚠️  SECURITY WARNING:")
    print("   - Your private key will be stored in a .env file")
    print("   - Keep this file secure and never share it")
    print("   - The .env file is already in .gitignore to prevent accidental commits")
    print()
    
    # Check if .env already exists
    env_file = Path(".env")
    if env_file.exists():
        print("📁 Found existing .env file")
        overwrite = input("Do you want to overwrite it? (y/n): ").lower().strip()
        if overwrite != 'y':
            print("❌ Setup cancelled")
            return
    
    print("🔑 Please provide your Coinbase wallet private key:")
    print("   - You can export this from Coinbase Wallet app")
    print("   - It should start with '0x' followed by 64 hex characters")
    print("   - Example: 0x1234567890abcdef...")
    print()
    
    # Get private key securely
    while True:
        private_key = getpass.getpass("Enter your private key (hidden input): ").strip()
        
        if not private_key:
            print("❌ Private key cannot be empty")
            continue
        
        if not private_key.startswith("0x"):
            print("❌ Private key should start with '0x'")
            continue
        
        if len(private_key) != 66:  # 0x + 64 hex chars
            print(f"❌ Private key should be 66 characters long (got {len(private_key)})")
            continue
        
        try:
            # Validate it's valid hex
            int(private_key[2:], 16)
            break
        except ValueError:
            print("❌ Private key contains invalid hex characters")
            continue
    
    # Create .env file content
    env_content = f"""# Flowbot Environment Configuration
# Your Coinbase wallet: 0xdBe52861b497b6D83f4757DB89ECC028896eccA4

# Your Coinbase wallet private key (KEEP THIS SECRET!)
PRIVATE_KEY={private_key}

# If using a proxy/funding address (e.g. email login), specify it here. Leave blank for direct wallet.
FUNDING_ADDRESS=

# Optional: CLOB API URL. Defaults to https://clob.polymarket.com
CLOB_API_URL=https://clob.polymarket.com

# Comma-separated list of token IDs (leave blank to use all active markets)
MARKET_IDS=
"""
    
    # Write .env file
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        
        # Set restrictive permissions (Unix-like systems)
        try:
            os.chmod(".env", 0o600)  # Read/write for owner only
        except:
            pass  # Windows doesn't support chmod
        
        print("✅ .env file created successfully!")
        print()
        print("📋 Next steps:")
        print("1. Make sure you have USDC in your Coinbase wallet on Polygon network")
        print("2. Run: python check_coinbase_wallet.py (to verify balance)")
        print("3. If you have USDC, you may need to approve the CLOB contract")
        print("4. Run: python -m flowbot.bot --iterations 1 (to test)")
        print()
        print("💡 Tips:")
        print("- Your wallet needs USDC on Polygon (not Ethereum mainnet)")
        print("- You don't need MATIC for gas fees with Polymarket's hybrid system")
        print("- The bot will ask for approval before each trade")
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return

if __name__ == "__main__":
    main() 