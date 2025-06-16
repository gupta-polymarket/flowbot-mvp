#!/usr/bin/env python3
"""
Wallet Scanner - Check what's actually in your wallet

This script will:
1. Check native token balances (MATIC, ETH)
2. Use a token scanner API to find all ERC20 tokens
3. Help identify where your USDC might be
"""
import os
import sys
import requests
from dotenv import load_dotenv
from web3 import Web3

def check_native_balances():
    """Check native token balances"""
    print("🔍 Checking Native Token Balances")
    print("=" * 40)
    
    # Load environment
    load_dotenv()
    
    # Get private key and derive address
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        print("❌ PRIVATE_KEY not found in environment")
        return
    
    # Get wallet address
    account = Web3().eth.account.from_key(private_key)
    wallet_address = account.address
    print(f"🏦 Wallet Address: {wallet_address}")
    print()
    
    # Check Polygon MATIC balance
    try:
        polygon_w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
        if polygon_w3.is_connected():
            matic_balance_wei = polygon_w3.eth.get_balance(wallet_address)
            matic_balance = matic_balance_wei / 10**18
            print(f"🟣 Polygon MATIC: {matic_balance:.6f} MATIC")
        else:
            print("❌ Failed to connect to Polygon")
    except Exception as e:
        print(f"❌ Error checking MATIC: {e}")
    
    # Check Ethereum ETH balance
    try:
        eth_w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
        if eth_w3.is_connected():
            eth_balance_wei = eth_w3.eth.get_balance(wallet_address)
            eth_balance = eth_balance_wei / 10**18
            print(f"🔵 Ethereum ETH: {eth_balance:.6f} ETH")
        else:
            print("❌ Failed to connect to Ethereum")
    except Exception as e:
        print(f"❌ Error checking ETH: {e}")
    
    return wallet_address

def check_polygon_tokens(wallet_address):
    """Check ERC20 tokens on Polygon using PolygonScan API"""
    print("\n🔍 Checking ERC20 Tokens on Polygon")
    print("=" * 40)
    
    try:
        # Use PolygonScan API to get token balances
        # Note: This is a free API but has rate limits
        url = f"https://api.polygonscan.com/api"
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': wallet_address,
            'startblock': 0,
            'endblock': 999999999,
            'sort': 'desc',
            'apikey': 'YourApiKeyToken'  # Free tier
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == '1' and data['result']:
                print("📋 Recent token transactions found:")
                
                # Get unique tokens from recent transactions
                tokens_seen = set()
                for tx in data['result'][:20]:  # Check last 20 transactions
                    token_symbol = tx.get('tokenSymbol', 'Unknown')
                    token_name = tx.get('tokenName', 'Unknown')
                    contract_address = tx.get('contractAddress', '')
                    
                    if token_symbol not in tokens_seen:
                        tokens_seen.add(token_symbol)
                        print(f"   🪙 {token_symbol} ({token_name})")
                        print(f"      Contract: {contract_address}")
                        
                        # If it's USDC-related, highlight it
                        if 'USDC' in token_symbol.upper():
                            print(f"      ⭐ This might be your USDC!")
                
                if not tokens_seen:
                    print("   ⚪ No token transactions found")
            else:
                print("   ⚪ No token transactions found")
        else:
            print(f"   ❌ API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking tokens: {e}")

def check_common_usdc_contracts(wallet_address):
    """Check common USDC contracts manually"""
    print("\n🔍 Checking Common USDC Contracts")
    print("=" * 40)
    
    # Common USDC contracts on Polygon
    usdc_contracts = {
        'USDC (old)': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
        'USDC (new)': '0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359',
        'USDC.e': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',  # Same as old
    }
    
    # ERC20 ABI for balance checking
    erc20_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        }
    ]
    
    try:
        w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
        
        for name, contract_address in usdc_contracts.items():
            try:
                contract = w3.eth.contract(
                    address=Web3.to_checksum_address(contract_address),
                    abi=erc20_abi
                )
                
                # Get token info
                symbol = contract.functions.symbol().call()
                decimals = contract.functions.decimals().call()
                
                # Get balance
                balance_raw = contract.functions.balanceOf(wallet_address).call()
                balance = balance_raw / (10 ** decimals)
                
                print(f"   🪙 {name} ({symbol}): {balance:.6f}")
                print(f"      Contract: {contract_address}")
                
                if balance > 0:
                    print(f"      💰 FOUND BALANCE: {balance:.6f} {symbol}")
                
            except Exception as e:
                print(f"   ❌ Error checking {name}: {e}")
                
    except Exception as e:
        print(f"❌ Error connecting to Polygon: {e}")

def main():
    """Main function"""
    print("🔍 Wallet Scanner - Finding your tokens")
    print("=" * 50)
    
    # Check native balances
    wallet_address = check_native_balances()
    
    if wallet_address:
        # Check ERC20 tokens
        check_polygon_tokens(wallet_address)
        
        # Check common USDC contracts
        check_common_usdc_contracts(wallet_address)
        
        print(f"\n💡 If you still can't find your USDC:")
        print(f"   1. Check your wallet on PolygonScan: https://polygonscan.com/address/{wallet_address}")
        print(f"   2. Check if it's on a different network (Ethereum, BSC, etc.)")
        print(f"   3. Verify the wallet address matches your expectation")

if __name__ == "__main__":
    main() 