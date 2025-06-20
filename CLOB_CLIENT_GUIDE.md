# Polymarket CLOB Client Implementation Guide

Based on real-world implementation experience from the Flowbot project, this guide documents key insights, common issues, and best practices for working with the py-clob-client for Polymarket trading.

## Architecture Overview

Polymarket uses a hybrid-decentralized CLOB system where orders are matched off-chain by operators and only settlement happens on-chain. Users do NOT need MATIC for gas fees to trade.

### Key Points:
- **Off-chain Order Matching**: Fast execution without gas fees
- **On-chain Settlement**: Final trades settled on Polygon
- **Proxy Authentication**: Email/Magic proxy mode (signature_type=1)
- **USDC Only**: No need for MATIC tokens

## Client Setup

### Environment Configuration

```bash
# .env file
PRIVATE_KEY=0xYourPrivateKeyHere
FUNDING_ADDRESS=0xYourDepositAddressHere  
CLOB_API_URL=https://clob.polymarket.com
```

### Client Initialization

```python
from py_clob_client.client import ClobClient

def setup_clob_client() -> ClobClient:
    private_key = os.getenv("PRIVATE_KEY")
    funding_address = os.getenv("FUNDING_ADDRESS")
    clob_host = os.getenv("CLOB_API_URL", "https://clob.polymarket.com")
    
    return ClobClient(
        host=clob_host,
        key=private_key,
        chain_id=137,           # Polygon mainnet
        signature_type=1,       # Email/Magic proxy
        funder=funding_address  # Your deposit address
    )
```

## Common Issues & Solutions

### 1. "Not Enough Balance / Allowance" Error

**Most common issue!** Occurs when:
- Wallet has 0 USDC (funds in Polymarket internal account)
- USDC allowance not set for CLOB contract

**Solutions:**
- Withdraw USDC from Polymarket account to wallet
- Deposit fresh USDC and approve CLOB contract allowance
- Use the correct deposit address from Polymarket web interface

### 2. "Invalid Amounts, Min Size: $1" Error

Polymarket requires minimum $1.00 orders:

```python
def validate_order_size(price: float, size: float) -> bool:
    total_cost = price * size
    if total_cost < 1.0:
        size = 1.0 / price  # Adjust to meet minimum
    return True
```

### 3. Order Constants Import Issues

```python
# Robust import pattern
try:
    from py_clob_client.order_builder.constants import BUY, SELL
except ImportError:
    BUY, SELL = "BUY", "SELL"  # Fallback
```

## Trading Patterns

### Market Order Execution

```python
def execute_trade(client: ClobClient, token_id: str, side: str, quantity: float):
    # Get orderbook
    orderbook = client.get_order_book(token_id)
    
    # Calculate price and size
    if side == "BUY":
        best_price = float(orderbook.asks[0].price)
        size = quantity / best_price
    else:
        best_price = float(orderbook.bids[0].price)
        size = quantity
    
    # Check for negative risk markets
    is_neg_risk = check_negative_risk_market(token_id)
    
    # Create order
    order_args = OrderArgs(
        price=best_price,
        size=size,
        side=side,
        token_id=token_id
    )
    
    if is_neg_risk:
        order_args.negrisk = True
    
    # Submit order
    signed_order = client.create_order(order_args)
    response = client.post_order(signed_order, OrderType.GTC)
    
    return getattr(response, 'orderId', None)
```

### Orderbook Analysis

```python
def analyze_orderbook(client: ClobClient, token_id: str):
    orderbook = client.get_order_book(token_id)
    
    # Key understanding:
    # Best BID = HIGHEST price someone will BUY for
    # Best ASK = LOWEST price someone will SELL for
    best_bid = float(orderbook.bids[0].price)
    best_ask = float(orderbook.asks[0].price)
    
    spread = best_ask - best_bid
    spread_pct = (spread / ((best_bid + best_ask) / 2)) * 100
    
    return {
        'best_bid': best_bid,
        'best_ask': best_ask,
        'spread': spread,
        'spread_pct': spread_pct
    }
```

## Best Practices

### 1. Rate Limiting
```python
@rate_limit(calls_per_second=1.5)
def get_orderbook_safe(client, token_id):
    return client.get_order_book(token_id)
```

### 2. Error Handling
```python
def robust_trade_execution(client, trade_params):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return execute_trade(client, **trade_params)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise
```

### 3. Session Management
```python
class TradingSession:
    def __enter__(self):
        logger.info("Starting trading session")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cancel_all_orders()
        self.print_session_summary()
```

## Trading Strategies

### Spread Tightening
Take best bid/ask orders to remove wide spreads:

```python
def find_spread_tightening_opportunities(orderbook, max_budget):
    orders_to_take = []
    remaining_budget = max_budget
    
    # Take asks from lowest price up (removes cheap sellers)
    for ask in orderbook['asks']:
        if remaining_budget <= 0:
            break
        
        cost = min(remaining_budget, ask['size'] * ask['price'])
        if cost >= 1.0:  # Meet minimum
            orders_to_take.append({
                'side': 'BUY',
                'price': ask['price'], 
                'cost': cost
            })
            remaining_budget -= cost
    
    return orders_to_take
```

### Market Making
Place limit orders around fair value:

```python
def create_market_making_orders(token_id, fair_value, spread_target=0.02):
    half_spread = spread_target / 2
    bid_price = fair_value * (1 - half_spread)
    ask_price = fair_value * (1 + half_spread)
    
    return [
        {'side': 'BUY', 'price': bid_price, 'size': 1.0},
        {'side': 'SELL', 'price': ask_price, 'size': 1.0}
    ]
```

## Key Takeaways

### ✅ Success Factors
- Use proxy authentication (signature_type=1)
- Respect $1.00 minimum order sizes
- Handle balance/allowance errors properly
- Implement rate limiting
- Validate token IDs (50+ digits)
- Check for negative risk markets

### ❌ Common Pitfalls
- Not setting funding address for proxy auth
- Orders below $1.00 minimum
- Missing rate limiting
- Not handling empty orderbooks
- Ignoring negative risk requirements
- Invalid price bounds (must be 0.0001-0.9999)

This guide represents battle-tested patterns from a fully operational Polymarket trading bot with proven success in order execution and market analysis. 