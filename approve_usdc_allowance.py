#!/usr/bin/env python3
"""
Script to approve USDC allowance for Polymarket CLOB contract
"""

import os
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("🔧 USDC Allowance Approval for Polymarket")
    print("=" * 50)
    
    # Get private key from environment
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print("❌ PRIVATE_KEY not found in .env file")
        print("💡 Run: python setup_coinbase_wallet.py first")
        return
    
    # Connect to Polygon
    polygon_rpc = "https://polygon-rpc.com"
    w3 = Web3(Web3.HTTPProvider(polygon_rpc))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Polygon network")
        return
    
    print("✅ Connected to Polygon network")
    
    # Get account from private key
    try:
        account = w3.eth.account.from_key(private_key)
        wallet_address = account.address
        print(f"🏦 Wallet Address: {wallet_address}")
    except Exception as e:
        print(f"❌ Invalid private key: {e}")
        return
    
    # USDC contract on Polygon
    usdc_address = w3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
    clob_address = w3.to_checksum_address("0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E")
    
    # USDC ABI (minimal - just what we need)
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
            "inputs": [
                {"name": "_owner", "type": "address"},
                {"name": "_spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
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
    
    # Get current balances and allowances
    try:
        decimals = usdc_contract.functions.decimals().call()
        balance_raw = usdc_contract.functions.balanceOf(wallet_address).call()
        balance_usdc = balance_raw / (10 ** decimals)
        
        allowance_raw = usdc_contract.functions.allowance(wallet_address, clob_address).call()
        allowance_usdc = allowance_raw / (10 ** decimals)
        
        print(f"💵 Current USDC Balance: {balance_usdc:.6f} USDC")
        print(f"✅ Current CLOB Allowance: {allowance_usdc:.6f} USDC")
        print(f"🏭 CLOB Contract: {clob_address}")
        
        if balance_usdc == 0:
            print("\n❌ No USDC found in wallet!")
            print("💡 You need to:")
            print("   1. Buy USDC on Coinbase")
            print("   2. Send it to your wallet on Polygon network")
            print(f"   3. Your wallet address: {wallet_address}")
            return
        
        if allowance_usdc >= balance_usdc:
            print(f"\n✅ Allowance is sufficient!")
            print(f"   Balance: {balance_usdc:.6f} USDC")
            print(f"   Allowance: {allowance_usdc:.6f} USDC")
            print("🎉 You're ready to trade!")
            return
        
        print(f"\n⚠️  Allowance needs to be increased")
        print(f"   Current allowance: {allowance_usdc:.6f} USDC")
        print(f"   Your balance: {balance_usdc:.6f} USDC")
        
        # Ask for approval amount
        print(f"\n🔧 How much USDC allowance do you want to approve?")
        print(f"   1. Approve exact balance ({balance_usdc:.6f} USDC)")
        print(f"   2. Approve unlimited (recommended for trading)")
        print(f"   3. Custom amount")
        
        while True:
            choice = input("Enter choice (1/2/3): ").strip()
            
            if choice == "1":
                approve_amount = balance_raw
                break
            elif choice == "2":
                # Max uint256 for unlimited approval
                approve_amount = 2**256 - 1
                break
            elif choice == "3":
                try:
                    custom_amount = float(input(f"Enter USDC amount to approve: "))
                    if custom_amount <= 0:
                        print("❌ Amount must be positive")
                        continue
                    approve_amount = int(custom_amount * (10 ** decimals))
                    break
                except ValueError:
                    print("❌ Invalid amount")
                    continue
            else:
                print("❌ Invalid choice")
                continue
        
        # Build transaction
        print(f"\n🔄 Preparing approval transaction...")
        
        # Get gas price and nonce
        gas_price = w3.eth.gas_price
        nonce = w3.eth.get_transaction_count(wallet_address)
        
        # Build transaction
        txn = usdc_contract.functions.approve(clob_address, approve_amount).build_transaction({
            'chainId': 137,  # Polygon
            'gas': 100000,   # Approval typically needs ~50k gas
            'gasPrice': gas_price,
            'nonce': nonce,
        })
        
        print(f"⛽ Estimated gas cost: {(txn['gas'] * gas_price) / 1e18:.6f} MATIC")
        
        # Check if we have enough MATIC for gas
        matic_balance = w3.eth.get_balance(wallet_address)
        gas_cost = txn['gas'] * gas_price
        
        if matic_balance < gas_cost:
            print(f"❌ Insufficient MATIC for gas!")
            print(f"   Need: {gas_cost / 1e18:.6f} MATIC")
            print(f"   Have: {matic_balance / 1e18:.6f} MATIC")
            print("💡 You need to get some MATIC for gas fees")
            return
        
        # Confirm transaction
        approve_display = "unlimited" if approve_amount == 2**256 - 1 else f"{approve_amount / (10 ** decimals):.6f}"
        print(f"\n📋 Transaction Summary:")
        print(f"   Approve: {approve_display} USDC")
        print(f"   Gas cost: {gas_cost / 1e18:.6f} MATIC")
        print(f"   To contract: {clob_address}")
        
        confirm = input("\n🤔 Confirm transaction? (y/n): ").lower().strip()
        if confirm != 'y':
            print("❌ Transaction cancelled")
            return
        
        # Sign and send transaction
        print("🔐 Signing transaction...")
        signed_txn = w3.eth.account.sign_transaction(txn, private_key)
        
        print("📡 Sending transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        print(f"⏳ Transaction sent: {tx_hash.hex()}")
        print("⏳ Waiting for confirmation...")
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt.status == 1:
            print("✅ Transaction successful!")
            print(f"🎉 USDC allowance approved!")
            print(f"🔗 Transaction: https://polygonscan.com/tx/{tx_hash.hex()}")
            
            # Verify new allowance
            new_allowance_raw = usdc_contract.functions.allowance(wallet_address, clob_address).call()
            new_allowance_usdc = new_allowance_raw / (10 ** decimals)
            print(f"✅ New allowance: {new_allowance_usdc:.6f} USDC")
            
            print("\n🎯 Next steps:")
            print("1. Run: python -m flowbot.bot --iterations 1")
            print("2. Test a small trade to make sure everything works")
            
        else:
            print("❌ Transaction failed!")
            print(f"🔗 Check transaction: https://polygonscan.com/tx/{tx_hash.hex()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return

if __name__ == "__main__":
    main() 