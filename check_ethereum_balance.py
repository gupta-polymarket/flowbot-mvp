#!/usr/bin/env python3
"""
Check USDC balance on Ethereum mainnet for both wallet addresses
"""

import os
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()



def main():
    print("🔍 Checking USDC on Ethereum Mainnet")
    print("=" * 50)
    
    # Wallet addresses
    flowbot_address = "0x5A1256113b1592a2a4D84Fe9C9Cb608dDDB9c0f3"
    coinbase_address = "0xdBe52861b497b6D83f4757DB89ECC028896eccA4"
    
    # Connect to Ethereum mainnet
    ethereum_rpc = "https://eth.llamarpc.com"
    w3 = Web3(Web3.HTTPProvider(ethereum_rpc))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Ethereum network")
        return
    
    print("✅ Connected to Ethereum mainnet")
    
    # USDC contract on Ethereum mainnet (correct address)
    usdc_address = w3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
    
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
    
    try:
        # Create contract instance
        usdc_contract = w3.eth.contract(address=usdc_address, abi=usdc_abi)
        
        # Get USDC decimals
        decimals = usdc_contract.functions.decimals().call()
        print(f"🪙 USDC Decimals: {decimals}")
        
        # Check both addresses
        for addr, label in [(flowbot_address, "Flowbot Wallet"), (coinbase_address, "Coinbase Wallet")]:
            print(f"\n📍 {label}: {addr}")
            
            # Get USDC balance
            balance_raw = usdc_contract.functions.balanceOf(addr).call()
            balance_usdc = balance_raw / (10 ** decimals)
            print(f"💵 USDC Balance: {balance_usdc:.6f} USDC")
            
            # Check ETH balance too
            eth_balance_wei = w3.eth.get_balance(addr)
            eth_balance = w3.from_wei(eth_balance_wei, 'ether')
            print(f"⛽ ETH Balance: {eth_balance:.6f} ETH")
            
            if balance_usdc > 0:
                print(f"✅ Found {balance_usdc:.6f} USDC on Ethereum!")
                print("💡 You'll need to bridge this to Polygon for Polymarket trading")
    
    except Exception as e:
        print(f"❌ Error checking Ethereum balances: {e}")
        print("🤔 This might be due to RPC issues or incorrect USDC address")
        print("💡 Your USDC is most likely in Polymarket's internal account system")

if __name__ == "__main__":
    main() 