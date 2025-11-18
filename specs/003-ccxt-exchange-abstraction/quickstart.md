# Quick Start: Multi-Exchange Trading with CCXT

This guide shows how to use the enhanced AlphaTransformer with multi-exchange support via CCXT abstraction layer.

## Overview

The multi-exchange system provides:
- **Unified interface** for trading across different exchanges
- **Backward compatibility** with existing single-exchange setup
- **Configuration-driven** exchange selection and management
- **Standardized data formats** across all exchanges

## Prerequisites

1. **Existing AlphaTransformer setup** with working Binance configuration
2. **Exchange accounts** with API access:
   - Binance Futures account with API key/secret
   - Hyperliquid account with wallet address and private key
3. **Environment variables** for credentials (recommended)

## Installation

### 1. Install CCXT Library
```bash
cd backend
pip install ccxt[all]  # Includes all exchange dependencies
pip install coincurve  # For optimized ECDSA signing (45ms → 0.05ms)
```

### 2. Verify CCXT Exchange Support
```python
import ccxt
print("Supported exchanges:", ccxt.exchanges)
# Should include both 'binance' and 'hyperliquid'
```

## Configuration

### 1. Environment Variables
Create `.env` file with exchange credentials:

```bash
# Binance Futures
BINANCE_API_KEY="your_binance_api_key"
BINANCE_SECRET="your_binance_secret"

# Hyperliquid  
HL_WALLET_ADDR="0xYourMainWalletAddress"
HL_PRIVATE_KEY="0xYourAPIWalletPrivateKey"
```

### 2. Enhanced Configuration File
Update `backend/config/agent.yaml`:

```yaml
# Backward compatible - existing configuration still works
exchange:
  name: "binance_futures"
  api_key: "${BINANCE_API_KEY}"
  api_secret: "${BINANCE_SECRET}"
  testnet: true
  default_leverage: 5

# New multi-exchange configuration (optional)
exchanges:
  binance_futures:
    ccxt_id: "binance"
    auth_type: "api_key"
    default_leverage: 1
    margin_mode: "cross"
    credentials:
      apiKey: "${BINANCE_API_KEY}"
      secret: "${BINANCE_SECRET}"
    options:
      defaultType: "future"
  hyperliquid:
    ccxt_id: "hyperliquid"
    auth_type: "wallet_key"
    default_leverage: 1
    margin_mode: "cross"
    credentials:
      wallet_address: "${HL_WALLET_ADDR}"
      private_key: "${HL_PRIVATE_KEY}"
    options:
      slippage: 0.02  # 2% max slippage for market orders
```

### 3. Hyperliquid Wallet & Private Key Setup
1. 在 [Hyperliquid Web](https://app.hyperliquid.xyz/portfolio) 里打开 **API Wallets**，创建一个新的 API Wallet。
2. 记录生成的 `walletAddress`（0x 开头）与 `privateKey`；它们只显示一次，立刻保存到你的密码管理器。
3. 将两个值写入 `.env` 或部署环境变量：
   ```bash
   export HL_WALLET_ADDR=0x1234...
   export HL_PRIVATE_KEY=0xabcdef...
   ```
4. 配置 `agent.yaml` 的 `exchanges.hyperliquid.credentials` 使用 `${HL_WALLET_ADDR}` 与 `${HL_PRIVATE_KEY}`。
5. 重启后即可通过 `get_exchange_trader("hyperliquid")` 使用钱包签名下单。

## Basic Usage

### 1. Backward Compatible Usage (No Code Changes)
Your existing agent code continues to work unchanged:

```python
# Existing code - no changes needed
from trading.binance_futures import get_trader

async def existing_agent_logic():
    trader = get_trader()  # Still works, returns Binance trader
    
    balance = await trader.get_balance()
    positions = await trader.get_positions()
    
    # All existing trading operations work the same
    result = await trader.open_long("BTC/USDT", quantity=0.001, leverage=5)
    print(f"Order result: {result}")
```

### 2. Enhanced Multi-Exchange Usage
Use the new factory pattern for multi-exchange trading:

```python
from trading.factory import get_exchange_trader

async def multi_exchange_agent():
    # Get specific exchange trader
    binance_trader = get_exchange_trader("binance_futures")
    hyperliquid_trader = get_exchange_trader("hyperliquid")
    
    # Check balances on both exchanges
    binance_balance = await binance_trader.get_balance()
    hyperliquid_balance = await hyperliquid_trader.get_balance()
    
    print(f"Binance balance: ${binance_balance.total_balance}")
    print(f"Hyperliquid balance: ${hyperliquid_balance.total_balance}")
    
    # Execute same strategy on both exchanges
    symbol = "BTC/USDT"
    quantity = 0.001
    
    # Open positions on both exchanges
    binance_result = await binance_trader.open_long(symbol, quantity, leverage=5)
    hyperliquid_result = await hyperliquid_trader.open_long(symbol, quantity, leverage=10)
    
    print(f"Binance order: {binance_result.status}")
    print(f"Hyperliquid order: {hyperliquid_result.status}")
```

### 3. Configuration-Driven Exchange Selection
```python
from trading.factory import get_exchange_trader
from config.settings import config

async def configurable_trading():
    # Legacy default (config.exchange.name)
    trader = get_exchange_trader()

    # Recommended: specify exchange explicitly  
    trader = get_exchange_trader("hyperliquid")
    
    balance = await trader.get_balance()
    print(f"Trading on {trader.get_exchange_name()}: ${balance.total_balance}")
```

## API Changes (Backward Compatible)

### 1. Enhanced Return Types
Trading operations now return standardized `OrderResult` objects:

```python
# New standardized return type
result = await trader.open_long("BTC/USDT", 0.001, leverage=5)

print(f"Order ID: {result.order_id}")
print(f"Status: {result.status}")
print(f"Executed: {result.executed_quantity} @ {result.executed_price}")
print(f"Fees: {result.fees}")
print(f"Exchange: {result.exchange}")
print(f"Raw data: {result.raw_data}")  # Exchange-specific details
```

### 2. Enhanced Data Objects
Position and balance objects include exchange information:

```python
positions = await trader.get_positions()
for pos in positions:
    print(f"Position on {pos.exchange}: {pos.symbol} {pos.side} {pos.size}")
    print(f"Liquidation price: {pos.liquidation_price}")
    print(f"Margin type: {pos.margin_type}")

balance = await trader.get_balance()
print(f"Balance on {balance.exchange}: ${balance.total_balance}")
print(f"Can trade: {balance.can_trade}")
print(f"Account type: {balance.account_type}")
```

### 3. New Utility Methods
Enhanced interface provides additional functionality:

```python
# Symbol validation
is_valid = await trader.validate_symbol("BTC/USDT")
print(f"BTC/USDT tradable: {is_valid}")

# Symbol format conversion
exchange_symbol = trader.normalize_symbol("BTC/USDT")
print(f"Exchange format: {exchange_symbol}")  # "BTCUSDT" for Binance, "BTC" for Hyperliquid

# Trading fees
fees = trader.get_trading_fees("BTC/USDT")
print(f"Maker: {fees.maker_fee}, Taker: {fees.taker_fee}")

# Precision formatting  
formatted_qty = trader.format_quantity("BTC/USDT", 0.123456789)
formatted_price = trader.format_price("BTC/USDT", 45123.456789)
print(f"Quantity: {formatted_qty}, Price: {formatted_price}")
```

## REST API Usage

### 1. Multi-Exchange Endpoints
```bash
# Get status of all exchanges
curl http://localhost:8000/trading/exchanges

# Get balance from specific exchange
curl http://localhost:8000/trading/exchanges/binance_futures/balance
curl http://localhost:8000/trading/exchanges/hyperliquid/balance

# Get positions from specific exchange
curl http://localhost:8000/trading/exchanges/hyperliquid/positions

# Execute order on specific exchange
curl -X POST http://localhost:8000/trading/exchanges/binance_futures/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USDT",
    "side": "open_long", 
    "quantity": 0.001,
    "leverage": 5,
    "order_type": "market"
  }'
```

### 2. Legacy Endpoints (Still Work)
```bash
# Existing endpoints use legacy default exchange (config.exchange.name)
curl http://localhost:8000/trading/balance
curl http://localhost:8000/trading/positions
```

## Migration Steps

### Step 1: Verify Current Setup
Ensure your existing Binance setup works:
```python
from trading.binance_futures import get_trader

trader = get_trader()
balance = await trader.get_balance()
print(f"Current balance: ${balance.total_balance}")
```

### Step 2: Add Hyperliquid Configuration
Add Hyperliquid settings to `agent.yaml` without changing existing config:
```yaml
# Keep existing exchange config
exchange:
  name: "binance_futures"
  # ... existing settings

# Add new exchanges section
exchanges:
  hyperliquid:
    # ... hyperliquid settings
```

### Step 3: Test Individual Exchanges
Test each exchange separately:
```python
# Test Binance (should work as before)
binance_trader = get_exchange_trader("binance_futures")
balance = await binance_trader.get_balance()
print(f"Binance: ${balance.total_balance}")

# Test Hyperliquid (new)
hyperliquid_trader = get_exchange_trader("hyperliquid") 
balance = await hyperliquid_trader.get_balance()
print(f"Hyperliquid: ${balance.total_balance}")
```

### Step 4: Gradually Enhance Agents
Enhance your agents to use multiple exchanges:
```python
# Start with one exchange
trader = get_exchange_trader("binance_futures")

# Later, add second exchange
traders = [
    get_exchange_trader("binance_futures"),
    get_exchange_trader("hyperliquid")
]

# Execute strategy across exchanges
for trader in traders:
    balance = await trader.get_balance()
    if balance.total_balance > 100:  # Only trade if sufficient balance
        await execute_strategy(trader)
```

## Testing

### 1. Unit Tests
Test exchange interface compliance:
```python
import pytest
from trading.factory import get_exchange_trader

@pytest.mark.asyncio
async def test_exchange_interface():
    """Test all exchanges implement interface correctly"""
    exchanges = ["binance_futures", "hyperliquid"]
    
    for exchange_name in exchanges:
        trader = get_exchange_trader(exchange_name)
        
        # Test basic interface
        assert hasattr(trader, 'get_balance')
        assert hasattr(trader, 'get_positions') 
        assert hasattr(trader, 'open_long')
        
        # Test exchange-specific methods
        assert await trader.validate_symbol("BTC/USDT")
        assert trader.get_exchange_name() == exchange_name
```

### 2. Integration Tests  
Test real exchange connections (with testnet/small amounts):
```python
@pytest.mark.integration  
async def test_real_trading():
    """Test actual trading operations"""
    trader = get_exchange_trader("binance_futures")  # Testnet
    
    # Small test trade
    result = await trader.open_long("BTC/USDT", 0.001, leverage=1)
    assert result.status == "FILLED"
    
    # Close the position
    close_result = await trader.close_long("BTC/USDT")
    assert close_result.status == "FILLED"
```

## Monitoring

### 1. Health Checks
Monitor exchange connectivity:
```python
async def monitor_exchanges():
    exchanges = ["binance_futures", "hyperliquid"]
    
    for name in exchanges:
        trader = get_exchange_trader(name)
        health = await trader.health_check()
        
        print(f"{name}: {health['status']} ({health['response_time_ms']}ms)")
        if health['status'] != 'healthy':
            print(f"Error: {health.get('error')}")
```

### 2. Performance Tracking
Track operation latencies:
```python
import time

async def time_operation(trader, operation_name, func):
    start = time.time()
    result = await func()
    duration = time.time() - start
    
    print(f"{trader.get_exchange_name()} {operation_name}: {duration:.3f}s")
    return result

# Usage
balance = await time_operation(trader, "get_balance", trader.get_balance)
```

## Troubleshooting

### Common Issues

1. **"Exchange not found" Error**
   - Check exchange name spelling in configuration
   - Verify exchange is enabled in config
   - Ensure credentials are set correctly

2. **"Authentication failed" Error**  
   - Verify environment variables are loaded
   - Check API permissions on exchange account
   - For Hyperliquid: ensure using API wallet private key, not main wallet

3. **"Symbol not found" Error**
   - Use internal format: "BTC/USDT" not "BTCUSDT"
   - Check symbol is available on target exchange
   - Use `validate_symbol()` method to verify

4. **Rate Limit Errors**
   - Reduce request frequency in configuration
   - Implement exponential backoff in retry logic
   - Monitor rate limit usage with monitoring endpoints

### Debug Mode
Enable verbose logging:
```python
import logging

logging.getLogger('ccxt').setLevel(logging.DEBUG)
logging.getLogger('trading').setLevel(logging.DEBUG)

# This will show all API requests/responses
trader = get_exchange_trader("hyperliquid")
balance = await trader.get_balance()
```

## Next Steps

1. **Add More Exchanges**: Use same pattern to add OKX, dYdX, etc.
2. **Portfolio Management**: Aggregate positions/balances across exchanges  
3. **Cross-Exchange Arbitrage**: Monitor price differences between exchanges
4. **Advanced Features**: Implement cross-exchange hedging strategies

For detailed implementation examples, see the full test suite in `tests/test_multi_exchange_integration.py`.
