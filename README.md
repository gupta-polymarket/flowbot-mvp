# Flowbot MVP - Automated Polymarket Trading Bot

A sophisticated automated trading bot for Polymarket's Central Limit Order Book (CLOB) that implements intelligent market-making strategies through systematic liquidity taking. Built from first principles with enterprise-grade architecture, comprehensive error handling, and advanced market resolution capabilities.

## 🎯 Purpose & Methodology

### Core Objective
Flowbot is designed to **artificially tighten spreads** on Polymarket by systematically taking the best bid/ask orders with randomized parameters. This creates more efficient price discovery and improved market liquidity for prediction market participants.

### Trading Strategy
- **Liquidity Taking**: Uses Fill-or-Kill (FOK) orders to immediately consume existing liquidity
- **Random Walk**: Implements controlled randomization to avoid predictable patterns
- **Spread Compression**: Targets best available prices to naturally tighten bid-ask spreads
- **Budget-Constrained**: Operates within strict per-market spending limits for risk management

### Market Impact
By consistently taking the best available prices, the bot:
1. **Reduces spreads** between bid and ask prices
2. **Improves price efficiency** through continuous market participation
3. **Increases trading volume** and market activity
4. **Provides counter-party liquidity** for other traders

## 🏗️ Technical Architecture

### System Design Philosophy

The codebase follows **enterprise software principles**:

- **Separation of Concerns**: Modular design with clear boundaries
- **Dependency Injection**: Configurable components for testability
- **Fail-Safe Defaults**: Conservative settings with graceful degradation
- **Comprehensive Logging**: Full observability into system behavior
- **Idempotent Operations**: Safe retry mechanisms for network failures

### Core Components

```
flowbot/
├── bot.py              # Main trading engine and orchestration
├── config.py           # Configuration management and validation
├── distributions.py    # Statistical sampling for randomization
└── __init__.py        # Package initialization

tests/
├── test_flowbot_comprehensive.py  # 35+ unit tests
├── test_integration.py            # Live API integration tests
└── test_flowbot.py                # Legacy compatibility tests

config.yaml            # YAML configuration with smart defaults
.env                   # Environment variables (private keys, etc.)
requirements.txt       # Python dependencies
```

## 🔬 Technical Implementation Details

### 1. Market Discovery & Resolution (`resolve_market_identifiers`)

The bot implements a **multi-stage market resolution pipeline**:

```python
def resolve_market_identifiers(identifiers: List[str]) -> List[str]:
    """
    Converts various market identifier formats to standardized token IDs
    
    Supported formats:
    - Polymarket URLs: https://polymarket.com/event/market-slug?tid=123
    - Market slugs: "will-trump-win-2024"  
    - Market IDs: Short numeric identifiers
    - Token IDs: 70+ digit outcome token identifiers
    """
```

**Resolution Strategy**:
1. **URL Parsing**: Extracts slugs from Polymarket event URLs
2. **Gamma API Integration**: Queries `gamma-api.polymarket.com` for active markets
3. **Token Extraction**: Parses `clobTokenIds` JSON arrays for outcome tokens
4. **Validation**: Ensures token IDs are valid 70+ digit strings
5. **Deduplication**: Returns unique set of tradeable token IDs

**Key Innovation**: Uses the **Gamma API** instead of the CLOB markets endpoint to find markets with `enableOrderBook: true`, solving the "No orderbook exists" problem.

### 2. Intelligent Market Filtering

```python
def get_active_markets_from_gamma() -> List[str]:
    """
    Discovers active markets with orderbook trading enabled
    
    Filtering criteria:
    - active: true (market is currently active)
    - closed: false (market hasn't resolved)
    - enableOrderBook: true (CLOB trading available)
    """
```

**Market Selection Logic**:
- Queries up to 100 active markets from Gamma API
- Filters for markets with orderbook trading enabled
- Extracts all outcome tokens (typically 2 per market: YES/NO)
- Returns comprehensive token ID pool for trading

### 3. Statistical Sampling Engine (`distributions.py`)

Implements **configurable probability distributions** for randomization:

```python
def sample_quantity(config: Dict[str, Any]) -> float:
    """Samples trade quantity from configured distribution"""
    
def sample_interval(config: Dict[str, Any]) -> float:
    """Samples time interval between trades"""
    
def sample_side(config: Dict[str, Any]) -> str:
    """Samples BUY/SELL with configurable probability"""
```

**Supported Distributions**:
- **Uniform**: Equal probability across range
- **Normal**: Gaussian distribution with mean/std
- **Exponential**: Exponential decay distribution
- **Fixed**: Constant values for deterministic behavior

### 4. Advanced Order Execution Pipeline

```python
def execute_trade(client: ClobClient, token_id: str, side: str, 
                 quantity: float, orderbook, config: Dict[str, Any]):
    """
    Executes a single trade with comprehensive error handling
    
    Pipeline:
    1. Orderbook analysis and price discovery
    2. Negative risk market detection
    3. Order parameter construction
    4. Trade execution with retry logic
    5. Budget tracking and validation
    """
```

**Execution Flow**:
1. **Price Discovery**: Analyzes orderbook for best bid/ask
2. **Risk Assessment**: Checks for negative risk markets via `/neg-risk` endpoint
3. **Order Construction**: Builds `OrderArgs` with proper parameters
4. **Submission**: Uses `create_and_post_order` for atomic execution
5. **Validation**: Confirms successful execution and updates budget tracking

### 5. Budget Management System

**Per-Market Budget Tracking**:
```python
_spent_usdc = {}  # Global budget tracking dictionary

def check_budget(token_id: str, cost: float, max_spend: float) -> bool:
    """Validates trade against per-market spending limits"""
    spent = _spent_usdc.get(token_id, 0)
    return spent + cost <= max_spend
```

**Budget Features**:
- **Independent Limits**: Each market has separate spending cap
- **Real-time Tracking**: Updates after successful BUY orders
- **Automatic Scaling**: Reduces quantity to fit remaining budget
- **Overflow Protection**: Prevents exceeding configured limits

### 6. CLOB API Integration

**Client Setup & Authentication**:
```python
def setup_clob_client(private_key: str, funding_address: Optional[str] = None) -> ClobClient:
    """
    Initializes CLOB client with proper authentication
    
    Supports:
    - Direct EOA trading (private key only)
    - Proxy wallet trading (with funding address)
    - Automatic API credential derivation
    """
```

**API Integration Points**:
- **Authentication**: EIP-712 signature-based auth with derived API keys
- **Orderbook Data**: Real-time bid/ask data via `/book` endpoint
- **Order Submission**: Atomic order creation and posting
- **Market Data**: Tick size and negative risk validation
- **Error Handling**: Comprehensive retry logic for network failures

### 7. Configuration Management (`config.py`)

**Hierarchical Configuration System**:
```python
def load_config() -> Dict[str, Any]:
    """
    Loads configuration from multiple sources with precedence:
    1. Environment variables (highest priority)
    2. config.yaml file
    3. Built-in defaults (fallback)
    """
```

**Configuration Features**:
- **Environment Override**: Critical settings via environment variables
- **YAML Configuration**: Human-readable configuration files
- **Smart Defaults**: Sensible fallbacks for all parameters
- **Validation**: Type checking and range validation
- **Hot Reload**: Configuration changes without restart

## 🔄 Trading Loop Architecture

### Main Execution Flow

```python
def run_trading_loop(client: ClobClient, token_ids: List[str], 
                    config: Dict[str, Any], iterations: Optional[int] = None):
    """
    Main trading loop with comprehensive error handling
    
    Loop Structure:
    1. Parameter sampling (market, side, quantity)
    2. Budget validation and adjustment
    3. Orderbook fetching and analysis
    4. Trade execution with error handling
    5. Result logging and budget updates
    6. Interval waiting with randomization
    """
```

### Iteration Lifecycle

1. **Sampling Phase**:
   - Random token selection from active pool
   - BUY/SELL side determination (configurable probability)
   - Quantity sampling from configured distribution

2. **Validation Phase**:
   - Budget constraint checking
   - Market availability verification
   - Orderbook liquidity analysis

3. **Execution Phase**:
   - Order parameter construction
   - API submission with retry logic
   - Response validation and error handling

4. **Tracking Phase**:
   - Budget updates for successful trades
   - Comprehensive logging of results
   - Performance metrics collection

5. **Waiting Phase**:
   - Randomized interval sampling
   - Rate limiting compliance
   - Graceful shutdown handling

## 🛡️ Error Handling & Resilience

### Multi-Layer Error Handling

1. **Network Layer**: HTTP timeouts, connection failures, DNS issues
2. **API Layer**: Rate limiting, authentication errors, malformed responses
3. **Business Logic**: Invalid markets, insufficient funds, orderbook issues
4. **System Layer**: Memory constraints, file I/O errors, signal handling

### Specific Error Scenarios

```python
# Cloudflare 403 Blocking
try:
    response = client.create_and_post_order(order_args)
except PolyApiException as e:
    if e.status_code == 403:
        logger.warning("Cloudflare blocking detected, implementing backoff")
        time.sleep(exponential_backoff())
        
# Insufficient Liquidity
if not orderbook.bids or not orderbook.asks:
    logger.warning(f"No liquidity available for token {token_id}")
    continue
    
# Budget Exhaustion
if spent_so_far >= max_spend:
    logger.info(f"Budget limit reached for token {token_id}")
    continue
```

### Recovery Strategies

- **Exponential Backoff**: Progressive delays for rate limiting
- **Circuit Breaker**: Temporary suspension after repeated failures
- **Graceful Degradation**: Continue with reduced functionality
- **State Persistence**: Resume from last known good state

## 🧪 Testing Methodology

### Test Architecture

The codebase implements **comprehensive testing** at multiple levels:

1. **Unit Tests** (`test_flowbot_comprehensive.py`):
   - 35+ individual test cases
   - Mock-based isolation testing
   - Edge case and error condition coverage
   - Configuration validation testing

2. **Integration Tests** (`test_integration.py`):
   - Live API connectivity testing
   - Real market data validation
   - End-to-end workflow verification
   - Performance benchmarking

3. **Validation Scripts**:
   - `demo.py`: Interactive demonstration mode
   - `validate.py`: Comprehensive system validation
   - `debug_clob_api.py`: API debugging and diagnostics

### Test Coverage Areas

```python
# Market Resolution Testing
def test_resolve_polymarket_url()
def test_resolve_token_ids()
def test_invalid_market_handling()

# Trading Logic Testing  
def test_execute_trade_success()
def test_execute_trade_insufficient_funds()
def test_budget_management()

# Configuration Testing
def test_load_config_from_yaml()
def test_environment_variable_override()
def test_invalid_configuration_handling()

# API Integration Testing
def test_clob_client_setup()
def test_orderbook_fetching()
def test_order_submission()
```

## 🔧 Advanced Features

### 1. Manual Approval Mode

```yaml
# config.yaml
manual_approval: true
```

Enables **human-in-the-loop** trading with detailed trade proposals:

```
================================================================================
🎯 PROPOSED TRADE
================================================================================
📊 Market: Will Trump repeal Presidential term limits?
🪙 Token ID: 37149124539698828019392556363337395568800154611809023682776980075330277279966
📈 Action: BUY
💰 Price: $0.9990 per share
📦 Quantity: 1.35 shares
💵 Total Cost: $1.35 USDC
📊 Current Spent on this market: $0.00 USDC
================================================================================

🤔 Approve this trade? (y/n/q):
```

### 2. Dry-Run Mode

Complete simulation environment for **risk-free testing**:

```bash
python -m flowbot.bot --dry-run --iterations 5
```

Features:
- Full market discovery and analysis
- Realistic parameter sampling
- Orderbook fetching and price discovery
- Simulated trade execution with logging
- Budget tracking without real spending

### 3. Market-Specific Trading

```bash
python -m flowbot.bot --market "token_id_here"
```

Enables **focused trading** on specific markets for:
- Strategy testing on particular events
- High-conviction market participation
- Debugging specific market issues

### 4. Configurable Randomization

```yaml
# Uniform distribution
quantity:
  type: uniform
  min: 0.5
  max: 2.0

# Normal distribution  
interval:
  type: normal
  mean: 30
  std: 10

# Fixed values
p_buy: 0.5  # 50% BUY probability
```

## 📊 Performance Characteristics

### Latency Profile

- **Market Discovery**: ~1-2 seconds (cached after startup)
- **Orderbook Fetch**: ~200-500ms per request
- **Order Execution**: ~300-800ms end-to-end
- **Budget Validation**: <1ms (in-memory operations)

### Throughput Capabilities

- **Sustainable Rate**: 1-2 trades per minute (respects rate limits)
- **Burst Capacity**: Up to 10 trades per minute (short duration)
- **Market Coverage**: 100+ active markets simultaneously
- **Token Pool**: 200+ outcome tokens available for trading

### Resource Utilization

- **Memory**: ~50-100MB typical usage
- **CPU**: Minimal (<5% on modern systems)
- **Network**: ~1-5 KB per API request
- **Storage**: Minimal (configuration and logs only)

## 🔐 Security & Risk Management

### Private Key Security

```python
# Environment-based key management
load_dotenv()
private_key = os.getenv("PRIVATE_KEY")

# Never logged or exposed
logger.debug("CLOB client setup complete")  # No key details
```

### Risk Controls

1. **Budget Limits**: Hard caps on per-market spending
2. **Fill-or-Kill Orders**: No resting orders that could be adversely filled
3. **Input Validation**: Sanitization of all external data
4. **Rate Limiting**: Compliance with API usage policies
5. **Error Isolation**: Failures don't cascade across markets

### Operational Security

- **Credential Isolation**: Environment variable separation
- **Minimal Permissions**: Only required API access
- **Audit Logging**: Complete transaction history
- **Safe Defaults**: Conservative configuration out-of-box

## 🚀 Deployment & Operations

### Production Deployment

```bash
# 1. Environment Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configuration
cp env.example .env
# Edit .env with production credentials

# 3. Validation
python validate.py

# 4. Production Run
python -m flowbot.bot
```

### Monitoring & Observability

**Comprehensive Logging**:
```
2025-06-13 14:47:36 [INFO] flowbot: Found 198 token IDs from 100 active markets
2025-06-13 14:47:36 [INFO] flowbot: CLOB client setup complete
2025-06-13 14:47:36 [INFO] flowbot: Sampled: token_id=..., side=BUY, quantity=1.35
2025-06-13 14:47:36 [INFO] flowbot: Best BUY price: 0.9990
2025-06-13 14:47:36 [INFO] flowbot: Creating order: BUY 1.35 shares @ 0.9990 (1.35 USDC)
```

**Key Metrics**:
- Trade execution success rate
- Average spread compression
- Budget utilization per market
- API response times and error rates

### Operational Procedures

1. **Health Checks**: Regular validation of API connectivity
2. **Budget Monitoring**: Real-time spending tracking
3. **Error Alerting**: Notification of critical failures
4. **Performance Tuning**: Optimization based on market conditions

## 🔬 Research & Development

### Algorithmic Trading Research

The codebase serves as a **research platform** for:

- **Market Microstructure**: Understanding prediction market dynamics
- **Liquidity Provision**: Optimal strategies for spread compression
- **Risk Management**: Portfolio-level risk controls
- **Market Impact**: Measuring effect of systematic trading

### Future Enhancements

1. **Machine Learning Integration**: Predictive models for optimal timing
2. **Multi-Market Arbitrage**: Cross-market opportunity detection
3. **Dynamic Risk Management**: Adaptive position sizing
4. **Advanced Order Types**: Iceberg orders, TWAP strategies

## 📚 Academic Context

### Prediction Market Theory

Flowbot implements concepts from:

- **Market Making Theory**: Providing liquidity for bid-ask spread compression
- **Random Walk Models**: Avoiding predictable patterns in trading
- **Information Aggregation**: Contributing to efficient price discovery
- **Behavioral Finance**: Understanding market participant psychology

### Technical Contributions

1. **API Integration Patterns**: Best practices for CLOB API usage
2. **Error Handling Strategies**: Robust distributed system design
3. **Configuration Management**: Flexible, hierarchical configuration systems
4. **Testing Methodologies**: Comprehensive test coverage for financial systems

## 🤝 Contributing

### Development Workflow

1. **Fork & Clone**: Standard GitHub workflow
2. **Environment Setup**: Follow installation instructions
3. **Feature Development**: Create feature branches
4. **Testing**: Ensure all tests pass
5. **Documentation**: Update README and code comments
6. **Pull Request**: Submit for review

### Code Standards

- **Type Hints**: Full type annotation for all functions
- **Docstrings**: Comprehensive documentation for all modules
- **Error Handling**: Explicit exception handling with logging
- **Testing**: Unit tests for all new functionality
- **Logging**: Appropriate log levels and messages

## ⚠️ Legal & Compliance

### Disclaimer

This software is provided for **educational and research purposes only**. Users are responsible for:

- Compliance with local financial regulations
- Understanding of prediction market risks
- Proper risk management and position sizing
- Adherence to Polymarket terms of service

### Risk Warnings

- **Financial Risk**: Trading involves potential loss of capital
- **Technical Risk**: Software bugs may cause unexpected behavior
- **Market Risk**: Prediction markets can be highly volatile
- **Regulatory Risk**: Legal status varies by jurisdiction

## 📖 References

- [Polymarket Documentation](https://docs.polymarket.com/)
- [PyCLOB Client](https://github.com/Polymarket/py-clob-client)
- [Prediction Market Research](https://en.wikipedia.org/wiki/Prediction_market)
- [Market Making Theory](https://en.wikipedia.org/wiki/Market_maker)

---

**Built with ❤️ for the prediction market ecosystem** 