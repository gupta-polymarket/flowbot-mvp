#!/usr/bin/env python3
"""
Find Deposit Address - Help locate the correct Polymarket funding address
"""
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

def find_deposit_address():
    """Help find the correct Polymarket deposit address"""
    print("🔍 Finding Polymarket Deposit Address")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    
    if not private_key:
        print("❌ PRIVATE_KEY not found in .env file")
        return False
    
    # Get wallet address from private key
    from eth_account import Account
    account = Account.from_key(private_key)
    wallet_address = account.address
    
    print(f"📍 Your private key corresponds to: {wallet_address}")
    print(f"💰 But your USDC might be in a different address!")
    
    print(f"\n🔍 How to find your Polymarket deposit address:")
    print("=" * 50)
    print("1. Go to https://polymarket.com")
    print("2. Log into your account (same account where you got the private key)")
    print("3. Look for 'Wallet' or 'Deposit' section")
    print("4. Find your 'Deposit Address' - this is where your USDC actually is")
    print("5. This deposit address is what you need as FUNDING_ADDRESS")
    
    print(f"\n📋 Steps to fix:")
    print("=" * 30)
    print("1. Copy your Polymarket deposit address")
    print("2. Add it to your .env file as:")
    print("   FUNDING_ADDRESS=0xYourDepositAddressHere")
    print("3. The bot will then use signature_type=1 with that funder address")
    
    print(f"\n🧪 Testing different proxy configurations:")
    print("=" * 50)
    
    # Test with some common proxy patterns
    test_addresses = [
        "0x0000000000000000000000000000000000000000",  # Placeholder
        wallet_address,  # Same as wallet (probably won't work)
    ]
    
    for i, test_addr in enumerate(test_addresses):
        print(f"\n🧪 Test {i+1}: Using {test_addr} as funder")
        
        try:
            # Test with signature_type=1 (Email/Magic)
            client = ClobClient(
                host="https://clob.polymarket.com",
                key=private_key,
                chain_id=137,
                signature_type=1,
                funder=test_addr
            )
            client.set_api_creds(client.create_or_derive_api_creds())
            
            # Try to get orderbook (read operation)
            token_id = "71685983838843709915160975671540060908877886707703474939962098991499689519711"
            orderbook = client.get_order_book(token_id)
            print(f"✅ Read operations work with funder {test_addr}")
            
        except Exception as e:
            print(f"❌ Failed with funder {test_addr}: {e}")
    
    print(f"\n💡 Next Steps:")
    print("=" * 20)
    print("1. 🌐 Go to Polymarket web interface")
    print("2. 📍 Find your actual deposit address") 
    print("3. 📝 Add FUNDING_ADDRESS=0xYourRealDepositAddress to .env")
    print("4. 🚀 Run the bot again")
    
    print(f"\n📚 Reference:")
    print("According to Polymarket docs, there are 3 client types:")
    print("- Direct EOA: Your private key = your funds address")
    print("- Email/Magic: Your private key ≠ your funds address (needs funder)")
    print("- Browser wallet: Your private key ≠ your funds address (needs funder)")
    print(f"\nSince you got balance/allowance error, you likely need the funder address!")

if __name__ == "__main__":
    find_deposit_address() 