# Flowbot - Automated Polymarket Trading Bot

🤖 **A fully functional automated trading bot for Polymarket** that randomly takes best bid/ask orders with configurable parameters to provide liquidity and tighten spreads.

## ✅ **Current Status: WORKING**

This bot is **fully operational** and successfully trading on Polymarket using:
- ✅ Email/Magic proxy authentication (signature_type=1)
- ✅ Price filtering (10¢ - 90¢ range)
- ✅ BUY-only mode (avoids balance issues)
- ✅ $1+ minimum orders (meets Polymarket requirements)
- ✅ Budget limits and manual approval

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

### 4. **Run the Bot**

```bash
# Activate virtual environment
source venv/bin/activate

# Test with dry run first
python -m flowbot.bot --dry-run --iterations 3

# Run actual trading
python -m flowbot.bot --iterations 10

# Run continuously (Ctrl+C to stop)
python -m flowbot.bot
```

## 📊 **How It Works**

### **Trading Flow:**
1. **Discovers active markets** from Gamma API
2. **Filters by price range** (10¢ - 90¢)
3. **Randomly selects** a market and trade size
4. **Fetches live orderbook** data
5. **Places market orders** (takes best bid/ask)
6. **Respects budget limits** per market
7. **Waits random interval** before next trade

### **Authentication:**
- Uses **Email/Magic proxy mode** (signature_type=1)
- Your **private key** signs orders
- Your **funding address** provides USDC
- No gas fees required (Polymarket pays)

### **Safety Features:**
- ✅ **Manual approval** for each trade
- ✅ **Budget limits** per market ($5 default)
- ✅ **Price filtering** (avoids extreme prices)
- ✅ **BUY-only mode** (avoids balance issues)
- ✅ **Minimum order size** ($1+ meets requirements)

## 🏗️ **Architecture**

```
flowbot/
├── __init__.py          # Package initialization
├── bot.py              # Main trading bot logic
├── config.py           # Configuration loading
├── distributions.py    # Random sampling functions
└── market_maker.py     # Market making strategies (optional)

config.yaml             # Trading configuration
env.example            # Environment template
requirements.txt       # Python dependencies
```

## ⚙️ **Configuration Options**

### **Trading Parameters:**
- `quantity`: Order size range (USDC)
- `interval`: Time between trades (seconds)
- `p_buy`: Probability of BUY vs SELL (0.0-1.0)
- `max_spend_per_market`: Budget limit per market
- `min_price`/`max_price`: Price filtering range
- `manual_approval`: Require manual approval

### **Command Line Options:**
```bash
python -m flowbot.bot [options]

Options:
  --market MARKET_ID    Trade specific market only
  --dry-run            Simulate without real trades
  --iterations N       Run N iterations then stop
```

## 🔧 **Troubleshooting**

### **Common Issues:**

**"not enough balance / allowance"**
- Check your FUNDING_ADDRESS is correct
- Verify USDC balance in your Polymarket account
- Make sure you're using the deposit address from Polymarket web interface

**"invalid amounts, min size: $1"**
- Increase `quantity.min` to 1.0 or higher
- Polymarket requires minimum $1 orders

**Orders getting rejected**
- Check price filtering range (10¢-90¢)
- Verify market has liquidity
- Ensure manual_approval is working

### **Getting Help:**
1. Check the logs for detailed error messages
2. Verify your `.env` configuration
3. Test with `--dry-run` first
4. Start with small quantities and budgets

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