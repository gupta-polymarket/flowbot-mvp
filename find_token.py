#!/usr/bin/env python3
"""
Active Token Finder - Find token IDs from currently ACTIVE Polymarket markets

Usage:
    python find_token.py "search term"
    python find_token.py --all  (show all active markets)
"""

import sys
import argparse
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime

def get_all_active_markets() -> List[Dict]:
    """Get all active markets from Gamma API"""
    print("🔄 Fetching active markets from Gamma API...")
    
    try:
        gamma_url = "https://gamma-api.polymarket.com/markets"
        response = requests.get(gamma_url, params={'limit': 500, 'active': 'true', 'closed': 'false'}, timeout=15)
        
        if response.status_code == 200:
            markets = response.json()
            
            # Filter for markets with tokens
            active_markets = []
            for market in markets:
                if market.get('active', False) and not market.get('closed', True):
                    clob_token_ids = market.get('clobTokenIds', '')
                    if isinstance(clob_token_ids, str) and clob_token_ids:
                        try:
                            token_list = json.loads(clob_token_ids)
                            if token_list:  # Has tokens
                                active_markets.append(market)
                        except json.JSONDecodeError:
                            continue
            
            print(f"✅ Found {len(active_markets)} active markets with tokens")
            return active_markets
            
    except Exception as e:
        print(f"❌ Failed to fetch active markets: {e}")
    
    return []

def search_active_markets(markets: List[Dict], search_term: str) -> List[Dict]:
    """Search active markets by term"""
    if not search_term:
        return markets
    
    search_lower = search_term.lower()
    matching_markets = []
    
    for market in markets:
        question = market.get('question', '').lower()
        description = market.get('description', '').lower()
        
        if search_lower in question or search_lower in description:
            matching_markets.append(market)
    
    return matching_markets

def display_markets(markets: List[Dict], context: str = ""):
    """Display markets with their tokens"""
    if not markets:
        print("❌ No active markets found")
        print("💡 Try a broader search term or use --all to see all active markets")
        return
    
    print(f"\n🎯 {context}")
    print("=" * 80)
    
    for i, market in enumerate(markets[:10]):  # Show max 10
        question = market.get('question', 'Unknown')
        end_date = market.get('endDate', 'Unknown')
        outcomes = market.get('outcomes', [])
        
        print(f"\n{i+1}. {question}")
        
        # Show end date
        if end_date != 'Unknown':
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                formatted_date = end_dt.strftime('%Y-%m-%d %H:%M UTC')
                print(f"    ⏰ Ends: {formatted_date}")
            except:
                print(f"    ⏰ Ends: {end_date}")
        
        # Show tokens
        clob_token_ids = market.get('clobTokenIds', '')
        if isinstance(clob_token_ids, str) and clob_token_ids:
            try:
                token_list = json.loads(clob_token_ids)
                
                print(f"    🟢 ACTIVE Tokens:")
                for j, token_id in enumerate(token_list):
                    outcome_name = outcomes[j] if j < len(outcomes) else f"Outcome {j+1}"
                    print(f"       {j+1}. {outcome_name}")
                    print(f"          Token ID: {token_id}")
                    print(f"          🚀 Trade: python -m flowbot.taker_bot --token-ids \"{token_id}\"")
                    
            except json.JSONDecodeError:
                print(f"    ❌ Could not parse tokens")
    
    if len(markets) > 10:
        print(f"\n... and {len(markets) - 10} more markets")
        print("Use a more specific search term to narrow results")

def main():
    parser = argparse.ArgumentParser(description="Find Token IDs from ACTIVE Polymarket Markets")
    parser.add_argument("--all", action="store_true", help="Show all active markets")
    parser.add_argument("--validate", help="Validate if a specific token ID is active")
    parser.add_argument("search_term", nargs="?", help="Search term to filter markets")
    
    args = parser.parse_args()
    
    print("🔍 Active Polymarket Token Finder")
    print("=" * 40)
    
    if args.validate:
        # Validate a specific token ID
        token_id = args.validate
        print(f"🔍 Checking if token is active: {token_id[:20]}...")
        
        markets = get_all_active_markets()
        is_active = False
        
        for market in markets:
            clob_token_ids = market.get('clobTokenIds', '')
            if isinstance(clob_token_ids, str) and clob_token_ids:
                try:
                    token_list = json.loads(clob_token_ids)
                    if token_id in [str(t) for t in token_list]:
                        is_active = True
                        print(f"✅ Token is ACTIVE and tradeable")
                        print(f"📊 Market: {market.get('question', 'Unknown')}")
                        print(f"🚀 Trade: python -m flowbot.taker_bot --token-ids \"{token_id}\"")
                        break
                except:
                    continue
        
        if not is_active:
            print(f"❌ Token is NOT ACTIVE (expired or closed)")
            
    else:
        # Get all active markets
        markets = get_all_active_markets()
        
        if not markets:
            print("❌ Could not fetch active markets")
            return
        
        if args.all:
            display_markets(markets, f"All {len(markets)} Active Markets")
        elif args.search_term:
            filtered_markets = search_active_markets(markets, args.search_term)
            display_markets(filtered_markets, f"Found {len(filtered_markets)} markets matching '{args.search_term}'")
        else:
            # Show a sample of markets
            sample_markets = markets[:5]
            display_markets(sample_markets, f"Sample of {len(sample_markets)} Active Markets (use --all to see all)")
            print(f"\n💡 Total active markets: {len(markets)}")
            print("💡 Use 'python find_token.py \"search term\"' to filter")
            print("💡 Use 'python find_token.py --all' to see all markets")

if __name__ == '__main__':
    main() 