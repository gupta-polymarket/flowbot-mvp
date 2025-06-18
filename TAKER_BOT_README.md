# Polymarket Taker Bot - Spread Tightening Specialist

🎯 **A specialized bot that tightens spreads by intelligently taking the best bid and ask orders up to $2 on each side.**

## 🎯 Purpose

The Taker Bot is designed to improve market efficiency by:
- **Tightening spreads** on Polymarket prediction markets
- **Taking liquidity** from orders that create wide spreads
- **Providing market efficiency** by removing orders far from fair value
- **Operating within controlled budgets** (max $2 per side)

## 🚀 Quick Start

### 1. **Setup Environment**

```bash
# Ensure you have the main flowbot setup complete
source venv/bin/activate
pip install -r requirements.txt

# Make sure your .env file is configured with:
# PRIVATE_KEY=your_polymarket_private_key
# FUNDING_ADDRESS=your_polymarket_deposit_address
```

### 2. **Run with Specific Markets**

```bash
# Target specific markets by URL
python -m flowbot.taker_bot --markets \
  "https://polymarket.com/event/presidential-election-winner" \
  "https://polymarket.com/event/another-market-url"
```

### 3. **Run with Random Market Discovery**

```bash
# Automatically discover and trade on active markets
python -m flowbot.taker_bot --iterations 10
```

### 4. **Test with Dry Run**

```bash
# Analyze markets without executing trades
python -m flowbot.taker_bot --dry-run --markets \
  "https://polymarket.com/event/some-market"
```

## 🎯 How It Works

### **Spread Analysis Strategy**

1. **Identifies Wide Spreads**: Finds markets with spreads larger than 1 cent
2. **Calculates Optimal Taking Points**: Determines which orders to take to tighten spreads
3. **Takes Strategic Orders**: 
   - Takes **bids** (by selling) that are close to mid-price
   - Takes **asks** (by buying) that are close to mid-price
4. **Respects Budget Limits**: Maximum $2 per side per iteration

### **Order Selection Algorithm**

The bot uses a sophisticated algorithm to identify orders to take:

```python
# Example: If current spread is $0.10
# Best Bid: $0.40, Best Ask: $0.50, Mid: $0.45

# Take bids above: $0.40 + ($0.10 * 0.25) = $0.425
# Take asks below: $0.50 - ($0.10 * 0.25) = $0.475

# This tightens the spread from $0.10 to ~$0.05
```

### **Market Selection**

**Option 1: Specific Markets**
```bash
--markets "url1" "url2" "url3"
```

**Option 2: Auto-Discovery**
```bash
# No --markets flag = random selection from active markets
```

## ⚙️ Configuration

### **Command Line Options**

```bash
python -m flowbot.taker_bot [options]

Options:
  --markets URL [URL ...]     Specific market URLs to target
  --max-spend FLOAT          Max spend per side in USDC (default: 2.0)
  --iterations INT           Number of iterations (default: infinite)
  --min-interval INT         Min seconds between iterations (default: 30)
  --max-interval INT         Max seconds between iterations (default: 60)
  --dry-run                  Simulate without executing trades
```

### **Configuration File**

Create `taker_config.yaml` for advanced settings:

```yaml
# Maximum spend per side
max_spend_per_side: 2.0

# Spread analysis parameters
spread_analysis:
  min_spread: 0.01           # Skip if spread < 1 cent
  taking_threshold: 0.25     # Take orders within 25% of spread
  
# Market filtering
market_discovery:
  min_price: 0.05           # Avoid extreme prices
  max_price: 0.95
```

## 📊 Example Session

```
🎯 SPREAD TIGHTENING ITERATION 1
============================================================

🎯 ANALYZING MARKET
📊 Market: Will Letitia James win the Democratic Primary for Mayor?
💹 Best Bid: $0.4200
💹 Best Ask: $0.5800
📏 Spread: $0.1600 (32.00%)
🎯 Mid Price: $0.5000

🎯 Found 2 spread-tightening opportunities

📈 SPREAD TIGHTENING ORDER
📊 Market: Will Letitia James win the Democratic Primary for Mayor?
🎯 Strategy: bid_taking
📋 Action: SELL
💰 Price: $0.4500
📦 Size: 4.44 shares
💵 Cost: $2.00

🤔 Execute this spread-tightening order? (y/n/q): y
✅ Order approved!
✅ Order executed successfully!
Order ID: 0x1234...

📈 SPREAD TIGHTENING ORDER
📊 Market: Will Letitia James win the Democratic Primary for Mayor?
🎯 Strategy: ask_taking
📋 Action: BUY
💰 Price: $0.5200
📦 Size: 3.85 shares
💵 Cost: $2.00

✅ Successfully executed 2 spread-tightening orders

📊 SESSION STATS
Iteration: 1
Total trades: 2
Markets traded: 1

⏰ Waiting 45 seconds until next iteration...
```

## 🎯 Strategy Details

### **Bid Taking (Selling)**
- **Identifies**: High bids that are above our threshold
- **Action**: SELL to those bidders
- **Effect**: Removes high bids, lowering the best bid closer to mid-price

### **Ask Taking (Buying)**
- **Identifies**: Low asks that are below our threshold  
- **Action**: BUY from those sellers
- **Effect**: Removes low asks, raising the best ask closer to mid-price

### **Budget Management**
- **Per Side Limit**: Maximum $2 on bid-taking, $2 on ask-taking
- **Per Order Minimum**: $1 minimum per order (Polymarket requirement)
- **Smart Allocation**: Distributes budget across multiple orders when beneficial

## 🛡️ Safety Features

- **Manual Approval**: Each trade requires confirmation (unless `--dry-run`)
- **Budget Limits**: Strict per-side spending limits
- **Spread Filtering**: Only targets markets with meaningful spreads
- **Price Validation**: Avoids extreme price markets
- **Order Minimums**: Respects Polymarket's $1 minimum order size

## 📊 Performance Tracking

The bot tracks:
- **Trades per market**
- **Total volume traded**
- **Session statistics**
- **Spread improvements achieved**

```
📊 FINAL SESSION SUMMARY
============================================================

🎯 Will Letitia James win the Democratic Primary for Mayor?
   Trades: 4
   Volume: $7.50

🎯 Bitcoin price above $100k by year end?
   Trades: 2
   Volume: $3.25

🎯 TOTALS
Markets: 2
Trades: 6
Volume: $10.75
============================================================
```

## 🔧 Advanced Usage

### **Target Specific Market Types**

```bash
# Focus on political markets
python -m flowbot.taker_bot --markets \
  "https://polymarket.com/event/presidential-election-winner" \
  "https://polymarket.com/event/senate-control"

# Focus on crypto markets  
python -m flowbot.taker_bot --markets \
  "https://polymarket.com/event/bitcoin-100k" \
  "https://polymarket.com/event/ethereum-5k"
```

### **Custom Spend Limits**

```bash
# Conservative: $1 per side
python -m flowbot.taker_bot --max-spend 1.0

# Aggressive: $5 per side
python -m flowbot.taker_bot --max-spend 5.0
```

### **Faster Execution**

```bash
# Trade every 5-10 seconds (very fast)
python -m flowbot.taker_bot --min-interval 5 --max-interval 10
```

## 🔗 Integration with Main Bot

The Taker Bot can be used alongside the main Flowbot:

```bash
# Terminal 1: Run spread tightening
python -m flowbot.taker_bot

# Terminal 2: Run general market making
python -m flowbot.bot
```

## 📈 Expected Impact

**Market Efficiency Improvements:**
- **Tighter Spreads**: Directly reduces bid-ask spreads
- **Better Price Discovery**: Removes orders far from fair value
- **Improved Liquidity**: Creates more efficient markets for other traders

**Risk Management:**
- **Limited Exposure**: Maximum $2 per side per iteration
- **Diversified**: Trades across multiple markets randomly
- **Controlled**: Manual approval prevents unwanted trades

---

**🎯 Ready to tighten those spreads!** Your specialized Polymarket taker bot is ready to improve market efficiency. 