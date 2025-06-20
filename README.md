# Flowbot - Comprehensive Polymarket Trading Bot Suite

🤖 **A complete suite of automated trading bots for Polymarket** featuring multiple trading strategies including random market taking, aggressive spread tightening, and market making capabilities.

## ✅ **Current Status: FULLY OPERATIONAL**

This bot suite is **production-ready** and successfully trading on Polymarket with:
- ✅ **Three Trading Modes**: Random taker, aggressive spread tightening, market making
- ✅ **Email/Magic Proxy Authentication** (signature_type=1) - no gas fees required
- ✅ **Comprehensive Market Discovery** via Gamma API and manual URL input
- ✅ **Advanced Budget Management** with per-market and per-side limits
- ✅ **Price Filtering & Risk Management** (configurable price bounds)
- ✅ **Real-time Orderbook Analysis** with spread impact tracking
- ✅ **Manual Approval Mode** for safe operation

## 🚀 **Quick Start**

### 1. **Setup Environment**

```bash
# Clone and setup
git clone <your-repo>
cd flowbot-mvp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Configure Environment**

Copy `env.example` to `.env` and fill in your details:

```bash
cp env.example .env
```

Edit `.env`:
```bash
# Your Polymarket private key (from web interface)
PRIVATE_KEY=0xYourPrivateKeyHere

# Your Polymarket deposit address (from web interface)
FUNDING_ADDRESS=0xYourDepositAddressHere

# API URL (default is fine)
CLOB_API_URL=https://clob.polymarket.com
```

### 3. **Configure Trading Parameters**

Edit `config.yaml`:

```yaml
# Trading parameters
quantity:
  type: uniform
  min: 1.0    # Minimum $1 USDC per trade
  max: 2.0    # Maximum $2 USDC per trade

# Time between trades (seconds)
interval:
  type: uniform
  min: 30     # Minimum 30 seconds
  max: 60     # Maximum 60 seconds

# Trading mode
p_buy: 1.0  # 1.0 = BUY only, 0.5 = 50/50 BUY/SELL

# Budget limits
max_spend_per_market: 5.0  # Max $5 per market

# Price filtering - only trade on reasonable prices
min_price: 0.10  # 10 cents minimum
max_price: 0.90  # 90 cents maximum

# Safety
manual_approval: true  # Approve each trade manually
```

### 4. **Choose Your Trading Strategy**

**Option A: Basic Random Taker Bot**
```bash
# Test with dry run first
python -m flowbot.bot --dry-run --iterations 3

# Run with specific iterations
python -m flowbot.bot --iterations 10

# Run continuously (Ctrl+C to stop)
python -m flowbot.bot
```

**Option B: Advanced Spread Tightening Bot**
```bash
# Target specific markets by URL
python -m flowbot.taker_bot --markets \
  "https://polymarket.com/event/presidential-election-winner"

# Auto-discover active markets
python -m flowbot.taker_bot --iterations 5

# Buy-only mode (safer, only takes ask orders)
python -m flowbot.taker_bot --buy-only --market-budget 3.0
```

**Option C: Market Making Bot**
```bash
# Provide liquidity with limit orders
python -c "
from flowbot.market_maker import run_market_maker
from flowbot.bot import setup_clob_client, get_active_markets_from_gamma
from flowbot.config import load_config

client = setup_clob_client()
config = load_config()
markets = get_active_markets_from_gamma()[:5]  # First 5 markets
run_market_maker(client, markets, config, iterations=10)
"
```

## 📊 **How It Works**

### **🎯 Trading Strategy Overview**

**1. Random Taker Bot (`flowbot.bot`)**
- Discovers active markets from Gamma API
- Randomly selects markets and trade sizes
- Takes best bid/ask orders (market orders)
- Configurable BUY/SELL probability
- Budget limits per market

**2. Spread Tightening Bot (`flowbot.taker_bot`)**
- Aggressively targets wide spreads
- Multiple trading rounds per market
- Takes best orders to force spread compression
- Detailed before/after analysis
- Buy-only mode for safer operation

**3. Market Making Bot (`flowbot.market_maker`)**
- Places limit orders around fair value
- Provides liquidity at multiple price levels
- Automatic order refresh and management
- Position limits and risk controls
- Configurable spread targets

### **🔐 Authentication & Infrastructure**
- **Email/Magic Proxy Mode** (signature_type=1) - recommended
- **Private Key Signing** - your key signs orders
- **Funding Address** - provides USDC for trades
- **No Gas Fees** - Polymarket covers all blockchain costs
- **Polygon Network** - fast execution, low costs

### **🛡️ Safety & Risk Management**
- ✅ **Manual Approval Mode** - confirm each trade
- ✅ **Budget Limits** - per-market and per-side spending caps
- ✅ **Price Filtering** - avoid extreme/illiquid prices
- ✅ **Order Minimums** - $1.00+ meets Polymarket requirements
- ✅ **Negative Risk Detection** - handles special market types
- ✅ **Rate Limiting** - prevents API throttling
- ✅ **Error Recovery** - robust retry mechanisms

## 🏗️ **Architecture**

```
flowbot-mvp/
├── flowbot/
│   ├── __init__.py          # Package initialization
│   ├── bot.py              # Main random taker bot
│   ├── taker_bot.py        # Advanced spread tightening bot
│   ├── market_maker.py     # Market making strategies
│   ├── config.py           # Configuration loading
│   └── distributions.py    # Random sampling functions
├── examples/
│   └── taker_bot_example.py # Usage examples
├── config.yaml             # Main bot configuration
├── taker_config.yaml       # Taker bot configuration
├── env.example            # Environment template
├── requirements.txt       # Python dependencies
├── README.md              # Main documentation
├── TAKER_BOT_README.md    # Taker bot detailed docs
└── CLOB_CLIENT_GUIDE.md   # CLOB client implementation guide
```

## ⚙️ **Complete Command Reference**

### **🎲 Random Taker Bot** (`python -m flowbot.bot`)

**Basic Usage:**
```bash
# Run with default settings (uses config.yaml)
python -m flowbot.bot

# Dry run (simulate without trading)
python -m flowbot.bot --dry-run

# Run specific number of iterations
python -m flowbot.bot --iterations 10

# Run with iteration limit
python -m flowbot.bot --max-iterations 5
```

**Market Selection:**
```bash
# Target specific market by URL
python -m flowbot.bot --market "https://polymarket.com/event/presidential-election-winner"

# Use multiple markets (set MARKET_IDS in .env)
MARKET_IDS="token_id_1,token_id_2" python -m flowbot.bot

# Auto-discover active markets (default behavior)
python -m flowbot.bot  # Uses Gamma API
```

### **🎯 Spread Tightening Bot** (`python -m flowbot.taker_bot`)

**Market Targeting:**
```bash
# Target specific markets by URL
python -m flowbot.taker_bot --markets \
  "https://polymarket.com/event/presidential-election-winner" \
  "https://polymarket.com/event/senate-control"

# Target by token IDs directly
python -m flowbot.taker_bot --token-ids \
  "12345...890" "09876...543"

# Auto-discover active markets
python -m flowbot.taker_bot --iterations 10
```

**Budget & Strategy Options:**
```bash
# Buy-only mode (safer, only takes ask orders)
python -m flowbot.taker_bot --buy-only

# Custom budget per market (default: $3)
python -m flowbot.taker_bot --market-budget 5.0

# Custom spend per side (default: $2)
python -m flowbot.taker_bot --max-spend 1.5

# Custom intervals between iterations
python -m flowbot.taker_bot --min-interval 5 --max-interval 15
```

**Analysis & Testing:**
```bash
# Dry run analysis
python -m flowbot.taker_bot --dry-run --markets \
  "https://polymarket.com/event/some-market"

# Single aggressive market processing
python -m flowbot.taker_bot --buy-only --token-ids "TOKEN_ID" \
  --iterations 1 --market-budget 10.0
```

### **🏭 Market Making Bot** (`flowbot.market_maker`)

Currently integrated as a module. Use programmatically:

```python
from flowbot.market_maker import run_market_maker
from flowbot.bot import setup_clob_client, get_active_markets_from_gamma
from flowbot.config import load_config

client = setup_clob_client()
config = load_config()
markets = get_active_markets_from_gamma()[:5]

# Run market maker
run_market_maker(client, markets, config, iterations=10)
```

## 📋 **Configuration Files**

### **Environment Variables** (`.env`)
```bash
# Required: Your Polymarket private key
PRIVATE_KEY=0xYourPrivateKeyFromPolymarketWebInterface

# Required: Your Polymarket deposit address (for proxy auth)
FUNDING_ADDRESS=0xYourDepositAddressFromPolymarketWebInterface

# Optional: CLOB API URL (default works)
CLOB_API_URL=https://clob.polymarket.com

# Optional: Comma-separated token IDs to trade
MARKET_IDS=token_id_1,token_id_2,token_id_3
```

### **Main Bot Configuration** (`config.yaml`)
```yaml
# Trading parameters
quantity:
  type: uniform
  min: 1.0    # Minimum $1 USDC per trade
  max: 2.0    # Maximum $2 USDC per trade

# Time between trades (seconds)
interval:
  type: uniform
  min: 30     # Minimum 30 seconds
  max: 60     # Maximum 60 seconds

# Trading behavior
p_buy: 1.0                   # 1.0 = BUY only, 0.5 = 50/50 BUY/SELL
max_spend_per_market: 5.0    # Budget limit per market (USDC)

# Price filtering - avoid extreme prices
min_price: 0.10    # Don't trade below 10 cents
max_price: 0.90    # Don't trade above 90 cents

# Safety features
manual_approval: true    # Require confirmation for each trade

# Market maker configuration
market_maker:
  order_size: 1.0          # Size per limit order (USDC)
  spread_target: 0.02      # Target spread (2%)
  max_position: 10.0       # Max position per token (USDC)
  price_levels: 3          # Number of price levels to quote
  refresh_interval: 30     # Seconds between order refreshes
```

### **Taker Bot Configuration** (`taker_config.yaml`)
```yaml
# Maximum spend per side per iteration
max_spend_per_side: 2.0

# Trading mode - only take ask orders (buy only)
buy_only: false

# Time between trading iterations (seconds)
interval:
  type: uniform
  min: 10
  max: 20

# Manual approval for each trade
manual_approval: true

# Spread analysis parameters
spread_analysis:
  min_spread: 0.005    # Minimum spread to consider (0.5 cents)

# Order execution parameters
order_execution:
  min_order_size: 1.0  # Minimum order size in USDC

# Market filtering (when using auto-discovery)
market_discovery:
  use_gamma_api: true
  min_price: 0.05      # Avoid extreme prices
  max_price: 0.95
```

## 🔧 **Troubleshooting**

### **❌ Common Issues & Solutions**

**"not enough balance / allowance"** - *Most common issue!*
- ✅ **Root Cause**: Wallet has 0 USDC (funds in Polymarket internal account) OR USDC allowance not set for CLOB contract
- ✅ **Solution**: Withdraw USDC from Polymarket account to wallet OR deposit fresh USDC and approve CLOB contract allowance
- ✅ **Prevention**: Use the correct deposit address from Polymarket web interface as `FUNDING_ADDRESS`

**"invalid amounts, min size: $1"**
- ✅ **Root Cause**: Polymarket requires minimum $1.00 orders
- ✅ **Solution**: Increase `quantity.min` to 1.0 or higher in config.yaml
- ✅ **Code Fix**: Bot automatically adjusts orders to meet minimums

**Orders getting rejected**
- ✅ **Check price filtering** range (10¢-90¢ default)
- ✅ **Verify market has liquidity** (check orderbook depth)
- ✅ **Ensure manual_approval is working** correctly
- ✅ **Validate token IDs** (should be 50+ digit numbers)

**Import errors with order constants**
- ✅ **Root Cause**: py-clob-client library version differences
- ✅ **Solution**: Bot has fallback handling for BUY/SELL constants
- ✅ **Update**: `pip install --upgrade py-clob-client`

### **🚀 Best Practices**
1. **Always test with `--dry-run` first**
2. **Start with small budgets** ($1-2 per market)
3. **Use manual approval mode** initially
4. **Monitor logs** for detailed error messages
5. **Check your `.env` configuration** carefully
6. **Verify USDC balance** in your Polymarket account

## 📈 **Performance**

**Successful Trading Record:**
- ✅ Order execution working
- ✅ Authentication stable
- ✅ Price filtering effective
- ✅ Budget management working
- ✅ Manual approval functional

**Example Successful Trade:**
```
🎯 PROPOSED TRADE
📊 Market: Will Letitia James win the Democratic Primary for Mayor of New York City?
📈 Action: BUY
💰 Price: $0.9990 per share
📦 Quantity: 1.33 shares
💵 Total Cost: $1.33 USDC

🎉 Order executed successfully!
Order ID: 0xea8700549a798d05bdec219b7bb0f9f7be80b257f480b9ab7c411ba44c6c3526
```

## 🛡️ **Security**

- **Private keys** stored in `.env` (never committed)
- **Manual approval** prevents unwanted trades
- **Budget limits** prevent excessive spending
- **Price filtering** avoids extreme/illiquid markets
- **Proxy authentication** (no direct wallet exposure)

## 📝 **License**

MIT License - See LICENSE file for details.

## 🎯 **Taker Bot - NEW!**

**Specialized spread tightening bot** that takes best bid/ask orders up to $2 on each side:

### **Quick Start**
```bash
# Target specific markets
python -m flowbot.taker_bot --markets \
  "https://polymarket.com/event/your-market-url"

# Auto-discover active markets
python -m flowbot.taker_bot --iterations 10

# Test without trading
python -m flowbot.taker_bot --dry-run
```

### **Features**
- 🎯 **Smart Spread Tightening**: Takes orders that create wide spreads
- 💰 **Budget Control**: Max $2 per side per iteration
- 🔄 **Market Discovery**: Auto-finds active markets or uses your URLs
- 📊 **Real-time Analysis**: Shows spread info and opportunities
- ✅ **Manual Approval**: Confirm each trade before execution

See [TAKER_BOT_README.md](TAKER_BOT_README.md) for detailed documentation.

---

## 🎯 **Next Steps**

- Monitor performance and adjust parameters
- Consider adding more sophisticated strategies
- Implement profit/loss tracking
- Add market-specific configurations
- Explore market making features

---

**🚀 Ready to trade! Your Polymarket bot is fully operational.** 