# Flowbot Mathematical Methodology & Algorithmic Design

## Overview

Flowbot is an **automated liquidity taker** designed to artificially tighten spreads on Polymarket by randomly taking best bid/ask orders. It operates as a **stochastic trading engine** that uses probabilistic sampling to simulate organic trading activity.

## Core Mathematical Framework

### 1. Stochastic Sampling Engine

Flowbot uses **uniform random distributions** for all key trading parameters:

#### Quantity Sampling
```
Q ~ U(q_min, q_max)
```
Where:
- `Q` = Trade quantity in USDC
- `U(a,b)` = Uniform distribution between a and b
- Default: `q_min = 0.1`, `q_max = 0.3` USDC

**Mathematical Implementation:**
```python
def sample_quantity(conf: Dict[str, Any]) -> float:
    q_conf = conf.get("quantity", {})
    return round(random.uniform(q_conf.get("min", 0.1), q_conf.get("max", 0.3)), 2)
```

#### Interval Sampling
```
T ~ U(t_min, t_max)
```
Where:
- `T` = Time interval between trades (seconds)
- Default: `t_min = 30`, `t_max = 60` seconds

#### Side Selection (Buy/Sell Probability)
```
P(BUY) = p_buy = 0.5 (default)
P(SELL) = 1 - p_buy = 0.5
```

**Bernoulli Trial Implementation:**
```python
def sample_side(conf: Dict[str, Any]) -> str:
    if random.random() < conf.get("p_buy", 0.5):
        return "BUY"
    return "SELL"
```

### 2. Market Selection Algorithm

#### Uniform Random Market Selection
```
M ~ U(M₁, M₂, ..., M_n)
```
Where `M_i` represents each available market token ID.

**Implementation:**
```python
token_id = random.choice(token_ids)  # Uniform selection from 198 active tokens
```

#### Market Discovery Process
1. **API Query**: `GET https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100`
2. **Filtering Criteria**:
   - `enableOrderBook = true`
   - `active = true`
   - `closed = false`
   - `clobTokenIds` exists and non-empty
3. **Token Extraction**: Parse `clobTokenIds` (JSON string → array)
4. **Result**: ~198 token IDs from ~100 active markets

### 3. Order Pricing Mechanism

#### Best Price Discovery
Flowbot uses **market-taking strategy** (always takes existing liquidity):

**For BUY Orders:**
```
P_execution = min(asks)  // Best ask price
Size_shares = Q_usdc / P_execution
```

**For SELL Orders:**
```
P_execution = max(bids)  // Best bid price
Size_shares = Q_usdc  // Direct quantity in shares
```

#### Price-Size Relationship
```
Total_Cost_USDC = {
    Q_usdc,                    if side = BUY
    Size_shares × P_execution, if side = SELL
}
```

### 4. Risk Management Framework

#### Per-Market Budget Constraints
```
Spent_i ≤ Max_Spend_Per_Market = $2.00 USDC (default)
```

Where `Spent_i` is cumulative spending on market `i`.

**Budget Enforcement Algorithm:**
```python
remaining_budget = max_spend - spent_so_far
if quantity > remaining_budget:
    quantity = remaining_budget  # Adjust to remaining budget
```

#### Position Tracking
```
Total_Spent = Σ(Spent_i) for all markets i
```

### 5. Temporal Dynamics

#### Inter-Trade Timing
```
Wait_Time ~ U(30, 60) seconds
```

This creates **Poisson-like arrival process** with variable intensity:
```
λ(t) ≈ 1/E[Wait_Time] = 1/45 ≈ 0.022 trades/second
```

Expected trades per hour: `λ × 3600 ≈ 80 trades/hour`

### 6. Order Execution Mathematics

#### Market Impact Model
Flowbot assumes **zero market impact** (price taker assumption):
- Orders execute at current best bid/ask
- No slippage consideration
- Immediate execution assumption

#### Order Size Optimization
```
Optimal_Size = min(
    Sampled_Quantity,
    Remaining_Budget,
    Available_Liquidity
)
```

### 7. Statistical Properties

#### Expected Value Calculations

**Expected Trade Size:**
```
E[Q] = (q_min + q_max) / 2 = (0.1 + 0.3) / 2 = 0.2 USDC
```

**Expected Inter-Trade Time:**
```
E[T] = (t_min + t_max) / 2 = (30 + 60) / 2 = 45 seconds
```

**Expected Trades Per Market:**
```
E[Trades_per_Market] = Max_Spend / E[Q] = 2.0 / 0.2 = 10 trades
```

#### Variance Calculations

**Quantity Variance:**
```
Var(Q) = (q_max - q_min)² / 12 = (0.3 - 0.1)² / 12 ≈ 0.0033
σ_Q ≈ 0.058 USDC
```

**Timing Variance:**
```
Var(T) = (t_max - t_min)² / 12 = (60 - 30)² / 12 = 75
σ_T ≈ 8.66 seconds
```

### 8. Liquidity Impact Theory

#### Spread Tightening Mechanism

**Before Flowbot:**
```
Spread = Ask_Price - Bid_Price
```

**After Flowbot Activity:**
```
New_Spread ≤ Original_Spread
```

**Mechanism**: By randomly taking both sides, Flowbot:
1. Removes stale orders at wide spreads
2. Forces market makers to requote tighter
3. Increases apparent trading volume
4. Reduces bid-ask spreads over time

#### Volume Amplification
```
Artificial_Volume = Σ(Q_i × P_i) for all executed trades i
```

This creates **synthetic liquidity** that appears as organic trading activity.

### 9. Market Microstructure Effects

#### Order Flow Randomization
```
Order_Flow(t) = {
    +Q_i if BUY at time t_i
    -Q_i if SELL at time t_i
    0    otherwise
}
```

#### Price Discovery Enhancement
By providing random order flow, Flowbot helps:
- **Reduce information asymmetry**
- **Increase price efficiency**
- **Improve market depth perception**

### 10. Configuration Parameters

| Parameter | Symbol | Default | Range | Distribution |
|-----------|--------|---------|-------|--------------|
| Quantity Min | q_min | 0.1 | [0.01, 1.0] | Uniform |
| Quantity Max | q_max | 0.3 | [0.1, 5.0] | Uniform |
| Interval Min | t_min | 30 | [1, 300] | Uniform |
| Interval Max | t_max | 60 | [30, 600] | Uniform |
| Buy Probability | p_buy | 0.5 | [0.0, 1.0] | Bernoulli |
| Max Spend | M_spend | 2.0 | [0.1, 100] | Fixed |

### 11. Performance Metrics

#### Success Rate
```
Success_Rate = Successful_Trades / Total_Attempts
```

#### Capital Efficiency
```
Capital_Efficiency = Total_Volume / Total_Capital_Deployed
```

#### Spread Impact
```
Spread_Improvement = (Spread_Before - Spread_After) / Spread_Before
```

## Algorithmic Flow

```
1. Initialize: Load config, connect to CLOB API
2. Market Discovery: Fetch active markets from Gamma API
3. Main Loop:
   a. Sample: token_id, side, quantity, interval
   b. Budget Check: Ensure within per-market limits
   c. Fetch Orderbook: Get current bids/asks
   d. Price Discovery: Find best execution price
   e. Order Creation: Build signed order
   f. Execution: Submit to CLOB
   g. Tracking: Update spending records
   h. Wait: Sleep for sampled interval
4. Repeat until stopped
```

## Mathematical Advantages

1. **Unpredictability**: Uniform random sampling prevents gaming
2. **Scalability**: Linear complexity O(n) in number of markets
3. **Risk Control**: Hard budget limits prevent runaway spending
4. **Market Neutrality**: Equal buy/sell probability maintains balance
5. **Liquidity Enhancement**: Consistent activity improves market quality

## Theoretical Foundation

Flowbot implements a **Monte Carlo approach** to market making, using:
- **Random sampling** for parameter selection
- **Market taking** for immediate execution
- **Budget constraints** for risk management
- **Temporal randomization** for natural behavior simulation

This creates an **artificial market participant** that enhances liquidity without directional bias, effectively serving as a **synthetic noise trader** that improves overall market microstructure. 