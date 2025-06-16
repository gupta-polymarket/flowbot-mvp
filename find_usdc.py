#!/usr/bin/env python3
"""
USDC Finder - Find USDC across different contracts and networks

This script checks for USDC in multiple places:
1. Native USDC on Polygon
2. Bridged USDC.e on Polygon  
3. USDC on Ethereum mainnet
4. Other common USDC variants
"""
import os
import sys
from dotenv import load_dotenv
from web3 import Web3

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# USDC contract addresses on different networks
USDC_CONTRACTS = {
    'Polygon': {
        'Native USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',  # Native USDC (6 decimals)
        'Bridged USDC.e': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',  # This is actually the same as native
        'USDC (new)': '0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359',  # New native USDC (6 decimals)
    },
    'Ethereum': {
        'USDC': '0xA0b86a33E6441b8C4505B4afDcA7FBf0251f7046',  # USDC on Ethereum
    }
}

# RPC endpoints
RPC_ENDPOINTS = {
    'Polygon': 'https://polygon-rpc.com',
    'Ethereum': 'https://eth.llamarpc.com',
}

# Minimal ERC20 ABI
ERC20_ABI = [
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
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

def check_token_balance(w3, contract_address, wallet_address, token_name):
    """Check balance for a specific token contract"""
    try:
        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=ERC20_ABI
        )
        
        # Get token info
        try:
            symbol = contract.functions.symbol().call()
            name = contract.functions.name().call()
            decimals = contract.functions.decimals().call()
        except:
            symbol = token_name
            name = token_name
            decimals = 6  # Default for USDC
        
        # Get balance
        balance_raw = contract.functions.balanceOf(wallet_address).call()
        balance = balance_raw / (10 ** decimals)
        
        return {
            'symbol': symbol,
            'name': name,
            'decimals': decimals,
            'balance': balance,
            'balance_raw': balance_raw,
            'contract': contract_address
        }
        
    except Exception as e:
        return {
            'symbol': token_name,
            'name': token_name,
            'decimals': 0,
            'balance': 0,
            'balance_raw': 0,
            'contract': contract_address,
            'error': str(e)
        }

def find_all_usdc():
    """Find USDC across all networks and contracts"""
    print("🔍 USDC Detective - Finding your USDC across networks")
    print("=" * 60)
    
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
    
    total_usdc_found = 0
    usdc_locations = []
    
    # Check each network
    for network_name, rpc_url in RPC_ENDPOINTS.items():
        print(f"🌐 Checking {network_name} Network...")
        print("-" * 40)
        
        try:
            # Connect to network
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not w3.is_connected():
                print(f"❌ Failed to connect to {network_name}")
                continue
            
            print(f"✅ Connected to {network_name}")
            
            # Check each USDC contract on this network
            if network_name in USDC_CONTRACTS:
                for token_name, contract_address in USDC_CONTRACTS[network_name].items():
                    print(f"   🔍 Checking {token_name}...")
                    
                    result = check_token_balance(w3, contract_address, wallet_address, token_name)
                    
                    if 'error' in result:
                        print(f"      ❌ Error: {result['error']}")
                    else:
                        balance = result['balance']
                        if balance > 0:
                            print(f"      💰 Found {balance:.6f} {result['symbol']} ({result['name']})")
                            print(f"         Contract: {result['contract']}")
                            total_usdc_found += balance
                            usdc_locations.append({
                                'network': network_name,
                                'token': token_name,
                                'balance': balance,
                                'contract': result['contract'],
                                'symbol': result['symbol']
                            })
                        else:
                            print(f"      ⚪ No balance in {result['symbol']}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error checking {network_name}: {e}")
            print()
    
    # Summary
    print("📊 SUMMARY")
    print("=" * 30)
    
    if total_usdc_found > 0:
        print(f"🎉 Total USDC Found: ${total_usdc_found:.6f}")
        print("\n📍 USDC Locations:")
        
        for location in usdc_locations:
            print(f"   • {location['network']}: {location['balance']:.6f} {location['symbol']} ({location['token']})")
            print(f"     Contract: {location['contract']}")
        
        # Check if any is on Polygon (needed for Polymarket)
        polygon_usdc = [loc for loc in usdc_locations if loc['network'] == 'Polygon']
        
        if polygon_usdc:
            print(f"\n✅ You have USDC on Polygon - ready for Polymarket!")
            for loc in polygon_usdc:
                print(f"   💰 {loc['balance']:.6f} {loc['symbol']} on Polygon")
        else:
            print(f"\n⚠️  No USDC found on Polygon")
            print("   💡 You'll need to bridge your USDC to Polygon for Polymarket trading")
            print("   🌉 Use: https://wallet.polygon.technology/polygon/bridge")
    else:
        print("❌ No USDC found in your wallet across all networks")
        print("\n💡 Next steps:")
        print("   1. Double-check your wallet address")
        print("   2. Buy USDC on an exchange")
        print("   3. Transfer to your wallet address")
    
    return usdc_locations

def main():
    """Main function"""
    locations = find_all_usdc()
    
    if locations:
        print(f"\n🔧 Technical Details:")
        print("For Polymarket trading, you need USDC on Polygon network")
        print("The balance checker was looking for Native USDC on Polygon")
        print("If you have USDC.e (bridged), that might explain the discrepancy")

if __name__ == "__main__":
    main() 