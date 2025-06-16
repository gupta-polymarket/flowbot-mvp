#!/usr/bin/env python3
"""
Get Funding Address - Find the correct funding address for Polymarket trading
"""
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
import requests

def get_funding_address():
    """Get the funding address for the Polymarket account"""
    print("💰 Getting Polymarket Funding Address")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    
    if not private_key:
        print("❌ PRIVATE_KEY not found in .env file")
        return False
    
    # Create client
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=private_key,
        chain_id=137
    )
    client.set_api_creds(client.create_or_derive_api_creds())
    
    print("✅ Client setup complete")
    
    # Get wallet address from private key
    from eth_account import Account
    account = Account.from_key(private_key)
    wallet_address = account.address
    print(f"📍 Wallet address: {wallet_address}")
    
    # Try to get funding address from the client
    try:
        # Check if the client has methods to get funding info
        print("\n🔍 Checking client methods for funding info...")
        
        # List available methods
        client_methods = [method for method in dir(client) if not method.startswith('_')]
        funding_methods = [method for method in client_methods if 'fund' in method.lower() or 'balance' in method.lower() or 'address' in method.lower()]
        
        if funding_methods:
            print(f"📋 Found potential funding methods: {funding_methods}")
            
            for method in funding_methods:
                try:
                    print(f"🧪 Trying {method}...")
                    result = getattr(client, method)()
                    print(f"✅ {method}: {result}")
                except Exception as e:
                    print(f"❌ {method} failed: {e}")
        else:
            print("ℹ️  No obvious funding methods found")
            
    except Exception as e:
        print(f"❌ Error checking client methods: {e}")
    
    # Try to make a direct API call to get user info
    try:
        print(f"\n🌐 Trying direct API calls...")
        
        # Get API credentials that the client uses
        api_creds = client.create_or_derive_api_creds()
        
        # Try to get user info
        headers = {
            'Authorization': f'Bearer {api_creds.key}',  # This might not be the right format
        }
        
        # Common endpoints that might give us funding info
        endpoints = [
            '/user',
            '/account', 
            '/balance',
            '/funding-address',
            '/wallet'
        ]
        
        for endpoint in endpoints:
            try:
                url = f"https://clob.polymarket.com{endpoint}"
                print(f"🔍 Trying {url}...")
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint}: {data}")
                    
                    # Look for funding address in response
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if 'address' in key.lower() or 'fund' in key.lower():
                                print(f"💰 Potential funding address: {key} = {value}")
                else:
                    print(f"❌ {endpoint}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {endpoint} failed: {e}")
                
    except Exception as e:
        print(f"❌ API calls failed: {e}")
    
    # Check Polymarket documentation approach
    print(f"\n📚 Based on Polymarket documentation:")
    print("1. For Email/Magic login: Use signature_type=1 with funder address")
    print("2. For Browser wallet: Use signature_type=2 with funder address") 
    print("3. For direct EOA: Should work without funder if USDC balance exists")
    
    print(f"\n💡 Next steps:")
    print("1. Check your Polymarket web interface for 'Deposit Address'")
    print("2. This deposit address should be used as FUNDING_ADDRESS")
    print("3. Make sure USDC is deposited to that address")
    print("4. Set USDC allowance for CLOB contract if needed")
    
    return wallet_address

if __name__ == "__main__":
    get_funding_address() 