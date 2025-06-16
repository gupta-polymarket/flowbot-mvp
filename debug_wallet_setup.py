#!/usr/bin/env python3
"""
Debug Wallet Setup - Understand the wallet configuration and balance issues
"""
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
import requests

def debug_wallet_setup():
    """Debug the wallet setup to understand balance/allowance issues"""
    print("🔍 Debugging Wallet Setup")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    funding_address = os.getenv("FUNDING_ADDRESS")
    
    if not private_key:
        print("❌ PRIVATE_KEY not found in .env file")
        return False
    
    print(f"✅ Private key loaded: {private_key[:10]}...")
    print(f"📋 Funding address: {funding_address or 'None (Direct EOA)'}")
    
    # Test different client configurations
    configurations = [
        {
            "name": "Direct EOA (no proxy)",
            "params": {
                "host": "https://clob.polymarket.com",
                "key": private_key,
                "chain_id": 137
            }
        },
        {
            "name": "Email/Magic proxy (signature_type=1)",
            "params": {
                "host": "https://clob.polymarket.com", 
                "key": private_key,
                "chain_id": 137,
                "signature_type": 1,
                "funder": funding_address if funding_address else "0x0000000000000000000000000000000000000000"
            }
        },
        {
            "name": "Browser wallet proxy (signature_type=2)",
            "params": {
                "host": "https://clob.polymarket.com",
                "key": private_key, 
                "chain_id": 137,
                "signature_type": 2,
                "funder": funding_address if funding_address else "0x0000000000000000000000000000000000000000"
            }
        }
    ]
    
    for config in configurations:
        print(f"\n🧪 Testing: {config['name']}")
        print("-" * 40)
        
        try:
            # Create client with this configuration
            client = ClobClient(**config['params'])
            print("✅ Client created successfully")
            
            # Set API credentials
            client.set_api_creds(client.create_or_derive_api_creds())
            print("✅ API credentials set")
            
            # Try to get a simple orderbook (read-only operation)
            token_id = "71685983838843709915160975671540060908877886707703474939962098991499689519711"
            orderbook = client.get_order_book(token_id)
            print("✅ Orderbook fetch successful")
            
            # Check if we can get user info or balances
            try:
                # This might give us insight into the account type
                print("🔍 Attempting to get account info...")
                # Note: py-clob-client might not have all methods, so we'll catch errors
                
            except Exception as e:
                print(f"ℹ️  Account info not available: {e}")
            
            print(f"✅ Configuration '{config['name']}' works for read operations")
            
        except Exception as e:
            print(f"❌ Configuration '{config['name']}' failed: {e}")
            
            # Check for specific error patterns
            if "signature" in str(e).lower():
                print("   🔐 Signature error - wrong key or proxy setup")
            elif "403" in str(e):
                print("   🛡️  Access denied - possible Cloudflare or auth issue")
            elif "balance" in str(e).lower():
                print("   💰 Balance/allowance issue")
    
    # Additional debugging: Check if the private key corresponds to a known address
    print(f"\n🔍 Additional Wallet Analysis")
    print("-" * 40)
    
    try:
        from eth_account import Account
        
        # Get the address from private key
        account = Account.from_key(private_key)
        address = account.address
        print(f"📍 Wallet address: {address}")
        
        # Check if this looks like a Polymarket proxy address pattern
        if address.lower().startswith('0x'):
            print("✅ Valid Ethereum address format")
        
        # Try to check USDC balance on Polygon (if we can)
        print("💰 Checking USDC balance on Polygon...")
        
        # Polygon USDC contract address
        usdc_contract = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
        
        # This would require web3 setup, so we'll skip for now
        print("ℹ️  USDC balance check requires web3 setup")
        
    except ImportError:
        print("ℹ️  eth_account not available for address analysis")
    except Exception as e:
        print(f"⚠️  Address analysis failed: {e}")
    
    print(f"\n💡 Recommendations:")
    print("1. If using Polymarket web interface private key, you likely need proxy setup")
    print("2. Check if your USDC is in Polymarket internal account vs wallet")
    print("3. Verify USDC allowance for CLOB contract")
    print("4. Consider using funding_address if available")

if __name__ == "__main__":
    debug_wallet_setup() 