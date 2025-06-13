#!/usr/bin/env python3
"""
Debug script to properly test CLOB API and find active markets
"""
import os
import sys
import requests
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_clob_api():
    """Test CLOB API endpoints to find active markets"""
    print("🔍 Debugging CLOB API Access")
    print("=" * 50)
    
    load_dotenv()
    gamma_host = "https://gamma-api.polymarket.com"
    
    # Test 1: Try the Gamma API for markets with enableOrderBook=true
    print("\n1. Testing Gamma API for markets with enableOrderBook=true...")
    try:
        # Get active markets with orderbooks enabled
        response = requests.get(f"{gamma_host}/markets?active=true&closed=false&limit=5", timeout=10)
        response.raise_for_status()
        gamma_markets = response.json()
        
        print(f"✅ Gamma API works")
        print(f"   Found {len(gamma_markets)} active, non-closed markets")
        
        for i, market in enumerate(gamma_markets[:3]):  # Show first 3 markets
            if isinstance(market, dict):
                enable_order_book = market.get("enableOrderBook", False)
                active = market.get("active", False)
                closed = market.get("closed", True)
                clob_token_ids = market.get("clobTokenIds", [])
                question = market.get("question", "Unknown")
                
                print(f"\n   Market {i+1}: {question[:50]}...")
                print(f"     enableOrderBook: {enable_order_book}")
                print(f"     active: {active}")
                print(f"     closed: {closed}")
                print(f"     clobTokenIds type: {type(clob_token_ids)}")
                print(f"     clobTokenIds value: {clob_token_ids}")
                
                if enable_order_book and active and not closed:
                    print(f"     ✅ This market qualifies for trading")
                    
                    # Try to parse clobTokenIds if it's a string
                    if isinstance(clob_token_ids, str):
                        try:
                            import json
                            parsed_tokens = json.loads(clob_token_ids)
                            print(f"     Parsed tokens: {parsed_tokens[:2]}...")  # Show first 2
                        except:
                            print(f"     Failed to parse as JSON")
                    elif isinstance(clob_token_ids, list):
                        print(f"     Already a list with {len(clob_token_ids)} items")
                        if clob_token_ids:
                            print(f"     First token: {clob_token_ids[0]}")
                else:
                    print(f"     ❌ Market not suitable for trading")
        
    except Exception as e:
        print(f"❌ Gamma API test failed: {e}")
        return
    
    print("\n" + "=" * 50)
    print("✅ Diagnostic complete!")

def test_orderbooks(active_markets):
    """Test orderbook access for active markets"""
    print("\n2. Testing orderbook access...")
    
    load_dotenv()
    clob_host = "https://clob.polymarket.com"
    
    working_tokens = []
    
    for market in active_markets[:5]:  # Test first 5 active markets
        print(f"\n   Testing market: {market['question'][:50]}...")
        
        for i, token_id in enumerate(market['token_ids']):
            print(f"     Token {i+1}: {token_id}")
            
            try:
                # Test direct API call
                response = requests.get(f"{clob_host}/book?token_id={token_id}", timeout=10)
                print(f"       Status: {response.status_code}")
                
                if response.status_code == 200:
                    book_data = response.json()
                    asks = book_data.get("asks", [])
                    bids = book_data.get("bids", [])
                    
                    print(f"       ✅ Orderbook exists! Asks: {len(asks)}, Bids: {len(bids)}")
                    
                    if asks or bids:
                        working_tokens.append({
                            "token_id": token_id,
                            "market": market['question'][:50],
                            "asks": len(asks),
                            "bids": len(bids)
                        })
                        
                        if asks:
                            print(f"          Best ask: {asks[0].get('price')} @ {asks[0].get('size')}")
                        if bids:
                            print(f"          Best bid: {bids[0].get('price')} @ {bids[0].get('size')}")
                
                elif response.status_code == 404:
                    print(f"       ❌ 404 - No orderbook")
                else:
                    print(f"       ❌ Error {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"       ❌ Exception: {e}")
    
    return working_tokens

def test_clob_client(working_tokens):
    """Test py-clob-client with working tokens"""
    print("\n3. Testing py-clob-client...")
    
    if not working_tokens:
        print("   ❌ No working tokens to test")
        return
    
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    clob_host = "https://clob.polymarket.com"
    
    if not private_key:
        print("   ❌ No PRIVATE_KEY found")
        return
    
    try:
        # Setup client
        client = ClobClient(host=clob_host, key=private_key, chain_id=137)
        client.set_api_creds(client.create_or_derive_api_creds())
        print("   ✅ Client setup successful")
        
        # Test with working tokens
        for token_info in working_tokens[:3]:  # Test first 3 working tokens
            token_id = token_info["token_id"]
            print(f"\n     Testing token: {token_id}")
            
            try:
                orderbook = client.get_order_book(token_id)
                print(f"       ✅ py-clob-client works!")
                
                asks = orderbook.get("asks", [])
                bids = orderbook.get("bids", [])
                print(f"       Asks: {len(asks)}, Bids: {len(bids)}")
                
                return token_info  # Return first working token
                
            except Exception as e:
                print(f"       ❌ py-clob-client failed: {e}")
    
    except Exception as e:
        print(f"   ❌ Client setup failed: {e}")
    
    return None

def main():
    """Run all diagnostic tests"""
    print("🚀 CLOB API Diagnostic")
    print("This will help us find the correct way to access live orderbooks")
    
    # Step 1: Find active markets
    test_clob_api()
    
    # Step 2: Test orderbook access
    working_tokens = test_orderbooks(active_markets)
    
    if not working_tokens:
        print("\n❌ No working orderbooks found!")
        print("This suggests the token IDs we're using are inactive/outdated")
        return
    
    # Step 3: Test py-clob-client
    working_token = test_clob_client(working_tokens)
    
    if working_token:
        print(f"\n🎉 SUCCESS! Found working token:")
        print(f"   Token ID: {working_token['token_id']}")
        print(f"   Market: {working_token['market']}")
        print(f"   Liquidity: {working_token['asks']} asks, {working_token['bids']} bids")
        
        print(f"\n📝 Update your config.yaml with:")
        print(f"markets:")
        print(f"  - \"{working_token['token_id']}\"")
        
        # Show other working tokens
        if len(working_tokens) > 1:
            print(f"\nOther working tokens:")
            for token in working_tokens[1:]:
                print(f"  - \"{token['token_id']}\"  # {token['market']}")
    
    else:
        print("\n❌ No working tokens found with py-clob-client")

if __name__ == "__main__":
    main() 