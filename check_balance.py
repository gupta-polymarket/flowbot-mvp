#!/usr/bin/env python3
"""
Balance Checker - Check wallet balance and allowances for trading

This script helps diagnose balance/allowance issues by checking:
1. USDC balance in wallet
2. USDC allowance for CLOB contract
3. Suggested actions to resolve issues
"""
import os
import sys
from dotenv import load_dotenv
from web3 import Web3
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowbot.bot import setup_clob_client

# USDC contract address on Polygon
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# USDC ABI (minimal - just what we need)
USDC_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
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

def check_wallet_balance():
    """Check USDC balance and allowances"""
    print("💰 Checking Wallet Balance & Allowances")
    print("=" * 50)
    
    try:
        # Load environment
        load_dotenv()
        
        # Get private key and derive address
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            print("❌ PRIVATE_KEY not found in environment")
            return
        
        # Setup Web3 connection to Polygon
        polygon_rpc = "https://polygon-rpc.com"
        w3 = Web3(Web3.HTTPProvider(polygon_rpc))
        
        if not w3.is_connected():
            print("❌ Failed to connect to Polygon network")
            return
        
        print("✅ Connected to Polygon network")
        
        # Get wallet address
        account = w3.eth.account.from_key(private_key)
        wallet_address = account.address
        print(f"🏦 Wallet Address: {wallet_address}")
        
        # Setup USDC contract
        usdc_contract = w3.eth.contract(
            address=Web3.to_checksum_address(USDC_ADDRESS),
            abi=USDC_ABI
        )
        
        # Get USDC decimals
        decimals = usdc_contract.functions.decimals().call()
        print(f"🪙 USDC Decimals: {decimals}")
        
        # Check USDC balance
        balance_raw = usdc_contract.functions.balanceOf(wallet_address).call()
        balance_usdc = balance_raw / (10 ** decimals)
        
        print(f"💵 USDC Balance: {balance_usdc:.6f} USDC")
        
        # Setup CLOB client to get contract address
        client = setup_clob_client()
        
        # The CLOB contract address (this is what needs allowance)
        # This might be in the client configuration
        clob_contract_address = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"  # Polymarket CLOB
        
        print(f"🏭 CLOB Contract: {clob_contract_address}")
        
        # Check allowance
        allowance_raw = usdc_contract.functions.allowance(
            wallet_address,
            Web3.to_checksum_address(clob_contract_address)
        ).call()
        allowance_usdc = allowance_raw / (10 ** decimals)
        
        print(f"✅ USDC Allowance: {allowance_usdc:.6f} USDC")
        
        # Analysis and recommendations
        print("\n📊 Analysis:")
        print("-" * 30)
        
        if balance_usdc < 1.0:
            print("⚠️  Low USDC balance - consider depositing more USDC")
            print(f"   Current: {balance_usdc:.6f} USDC")
            print(f"   Recommended: At least 10-50 USDC for trading")
        else:
            print(f"✅ USDC balance looks good: {balance_usdc:.6f} USDC")
        
        if allowance_usdc < balance_usdc:
            print("⚠️  Insufficient allowance - need to approve CLOB contract")
            print(f"   Current allowance: {allowance_usdc:.6f} USDC")
            print(f"   Available balance: {balance_usdc:.6f} USDC")
            print("   💡 Solution: Approve CLOB contract to spend your USDC")
        else:
            print(f"✅ Allowance looks good: {allowance_usdc:.6f} USDC")
        
        # Check if we have enough for a small trade
        min_trade_amount = 1.0  # $1 minimum
        if balance_usdc >= min_trade_amount and allowance_usdc >= min_trade_amount:
            print(f"\n🎉 Ready to trade! You have sufficient balance and allowance")
        else:
            print(f"\n❌ Not ready to trade yet")
            if balance_usdc < min_trade_amount:
                print(f"   - Need more USDC (have {balance_usdc:.6f}, need {min_trade_amount})")
            if allowance_usdc < min_trade_amount:
                print(f"   - Need to approve allowance (have {allowance_usdc:.6f}, need {min_trade_amount})")
        
        return {
            'balance': balance_usdc,
            'allowance': allowance_usdc,
            'wallet_address': wallet_address,
            'ready_to_trade': balance_usdc >= min_trade_amount and allowance_usdc >= min_trade_amount
        }
        
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        return None

def main():
    """Main function"""
    print("🔍 Flowbot Balance Checker")
    print("This will help diagnose balance/allowance issues\n")
    
    result = check_wallet_balance()
    
    if result and not result['ready_to_trade']:
        print("\n💡 Next Steps:")
        print("1. If you need USDC, buy some on an exchange and transfer to your wallet")
        print("2. If you need to approve allowance, you can do this through:")
        print("   - Polymarket website (connect wallet and it will prompt)")
        print("   - Or use a script to approve the CLOB contract")
        print("\n🌐 Polymarket CLOB Contract: 0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E")

if __name__ == "__main__":
    main() 