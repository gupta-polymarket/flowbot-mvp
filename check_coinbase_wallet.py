#!/usr/bin/env python3
"""
Check balance of Coinbase wallet address
"""

import os
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("🔍 Checking Coinbase Wallet Balance")
    print("=" * 50)
    
    # Coinbase wallet address
    coinbase_address = "0xdBe52861b497b6D83f4757DB89ECC028896eccA4"
    
    # Connect to Polygon
    polygon_rpc = "https://polygon-rpc.com"
    w3 = Web3(Web3.HTTPProvider(polygon_rpc))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Polygon network")
        return
    
    print(f"✅ Connected to Polygon network")
    print(f"🏦 Coinbase Wallet: {coinbase_address}")
    
    # USDC contract on Polygon
    usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    
    # USDC ABI (minimal)
    usdc_abi = [
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
        }
    ]
    
    # Create contract instance
    usdc_contract = w3.eth.contract(address=usdc_address, abi=usdc_abi)
    
    # Get USDC decimals
    decimals = usdc_contract.functions.decimals().call()
    print(f"🪙 USDC Decimals: {decimals}")
    
    # Get USDC balance
    balance_raw = usdc_contract.functions.balanceOf(coinbase_address).call()
    balance_usdc = balance_raw / (10 ** decimals)
    
    print(f"💵 USDC Balance: {balance_usdc:.6f} USDC")
    
    # Check MATIC balance too
    matic_balance_wei = w3.eth.get_balance(coinbase_address)
    matic_balance = w3.from_wei(matic_balance_wei, 'ether')
    print(f"⛽ MATIC Balance: {matic_balance:.6f} MATIC")
    
    print("\n📊 Analysis:")
    print("-" * 30)
    
    if balance_usdc > 0:
        print(f"✅ Found {balance_usdc:.6f} USDC in Coinbase wallet!")
        print("💡 This explains why your Flowbot wallet shows 0 USDC")
        print("🔄 You need to transfer USDC from Coinbase to your Flowbot wallet")
        print(f"   From: {coinbase_address}")
        print(f"   To:   0x5A1256113b1592a2a4D84Fe9C9Cb608dDDB9c0f3")
    else:
        print("❌ No USDC found in Coinbase wallet either")
        print("🤔 Your USDC might be:")
        print("   - In Polymarket's internal account system")
        print("   - On a different network (Ethereum mainnet)")
        print("   - In a different wallet")
    
    if matic_balance > 0:
        print(f"✅ Found {matic_balance:.6f} MATIC for gas fees")
    else:
        print("⚠️  No MATIC found - you'll need some for transfers")

if __name__ == "__main__":
    main() 