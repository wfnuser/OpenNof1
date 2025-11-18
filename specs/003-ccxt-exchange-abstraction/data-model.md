# Data Model: CCXT Exchange Abstraction

**Feature**: Multi-exchange trading abstraction with Hyperliquid support
**Date**: 2025-11-18
**Status**: Design Phase

## Core Entities

### ExchangeTrader (Interface)
**Purpose**: Unified interface for all trading operations across different exchanges

**Key Attributes**:
- `exchange_name: str` - Exchange identifier (e.g., "binance_futures", "hyperliquid")
- `is_connected: bool` - Connection status to exchange
- `supported_symbols: List[str]` - List of tradable symbols on this exchange

**Key Methods**:
- Trading operations: `open_long()`, `open_short()`, `close_long()`, `close_short()`
- Data retrieval: `get_balance()`, `get_positions()`, `get_market_price()`
- Configuration: `set_leverage()`, `set_margin_mode()`
- Validation: `validate_symbol()`, `format_quantity()`, `normalize_symbol()`

**Relationships**:
- **Implements** → Trading operations for specific exchanges
- **Returns** → OrderResult, Balance, Position objects
- **Uses** → ExchangeConfiguration for settings

**State Transitions**:
```
Disconnected → Connected (via authentication)
Connected → Trading (via successful market data fetch)
Trading → Error (via network/API failures)
Error → Connected (via retry/reconnection)
```

### ExchangeConfiguration (Data Class)
**Purpose**: Exchange-specific settings including credentials, API endpoints, and trading parameters

**Key Attributes**:
- `name: str` - Exchange identifier
- `auth_type: str` - Authentication method ("api_key", "rsa_key", "wallet_key")
- `credentials: Dict[str, str]` - Authentication credentials (environment variables)
- `testnet: bool` - Whether to use testnet/sandbox mode
- `rate_limits: RateLimit` - API rate limiting configuration
- `trading_params: TradingParameters` - Exchange-specific trading settings

**Validation Rules**:
- `name` must be non-empty and match supported exchange list
- `auth_type` must be valid for the exchange type
- `credentials` must contain required fields for auth_type
- `rate_limits` must have positive values for all limits

**Relationships**:
- **Used by** → ExchangeTrader implementations
- **Contains** → RateLimit, TradingParameters
- **Validated by** → ConfigurationValidator

### OrderResult (Data Class)
**Purpose**: Standardized representation of trading order execution results across exchanges

**Key Attributes**:
- `symbol: str` - Trading pair symbol
- `order_id: str` - Exchange-specific order identifier
- `client_order_id: str` - Client-specified order identifier
- `side: str` - "BUY" or "SELL"
- `order_type: str` - "MARKET", "LIMIT", "STOP", etc.
- `quantity: float` - Requested order quantity
- `price: Optional[float]` - Order price (None for market orders)
- `executed_quantity: float` - Actually executed quantity
- `executed_price: Optional[float]` - Average execution price
- `status: str` - "FILLED", "PARTIALLY_FILLED", "CANCELLED", "FAILED"
- `fees: float` - Trading fees paid
- `timestamp: datetime` - Order execution timestamp
- `exchange: str` - Exchange where order was executed
- `raw_data: Dict[str, Any]` - Original exchange response data

**Validation Rules**:
- `quantity` and `executed_quantity` must be non-negative
- `status` must be one of predefined status values
- `side` must be "BUY" or "SELL"
- `timestamp` must be valid datetime

**Relationships**:
- **Returned by** → All ExchangeTrader trading operations
- **Contains** → Exchange-specific data in raw_data field
- **Used by** → Trading agents for decision making

### Position (Enhanced Data Class)
**Purpose**: Standardized position information across exchanges (extends existing Position class)

**Key Attributes** (existing):
- `symbol: str` - Trading pair symbol
- `side: str` - "LONG" or "SHORT"
- `size: float` - Position size
- `entry_price: float` - Average entry price
- `mark_price: float` - Current market price
- `unrealized_pnl: float` - Unrealized profit/loss
- `percentage_pnl: float` - PnL as percentage
- `leverage: float` - Leverage multiplier
- `margin: float` - Margin used for position
- `timestamp: datetime` - Position data timestamp

**Enhanced Attributes** (new):
- `exchange: str` - Exchange where position is held
- `position_id: Optional[str]` - Exchange-specific position identifier
- `liquidation_price: Optional[float]` - Liquidation price if available
- `margin_type: str` - "cross" or "isolated"
- `raw_data: Dict[str, Any]` - Exchange-specific position data

**Validation Rules**:
- `size` must be positive
- `side` must be "LONG" or "SHORT"
- `leverage` must be positive
- `exchange` must be valid exchange identifier

**Relationships**:
- **Returned by** → ExchangeTrader.get_positions()
- **Used by** → Position service and trading agents
- **Contains** → Exchange-specific data for debugging

### Balance (Enhanced Data Class) 
**Purpose**: Standardized account balance information (extends existing Balance class)

**Key Attributes** (existing):
- `total_balance: float` - Total account balance
- `available_balance: float` - Available for trading
- `margin_balance: float` - Balance including unrealized PnL
- `unrealized_pnl: float` - Total unrealized profit/loss
- `currency: str` - Balance currency (typically "USDT")
- `timestamp: datetime` - Balance data timestamp

**Enhanced Attributes** (new):
- `exchange: str` - Exchange account
- `margin_used: float` - Currently used margin
- `maintenance_margin: float` - Required maintenance margin
- `can_trade: bool` - Whether account can place new trades
- `account_type: str` - "futures", "spot", "margin", etc.
- `raw_data: Dict[str, Any]` - Exchange-specific balance data

**Validation Rules**:
- All balance amounts must be non-negative
- `available_balance` ≤ `total_balance`
- `currency` must be valid currency code
- `exchange` must be valid exchange identifier

**Relationships**:
- **Returned by** → ExchangeTrader.get_balance()
- **Used by** → Risk management and position sizing
- **Aggregated by** → Multi-exchange portfolio view

### SymbolMapping (Configuration Entity)
**Purpose**: Maps internal symbol format to exchange-specific formats

**Key Attributes**:
- `internal_symbol: str` - Standard internal format (e.g., "BTC/USDT")
- `exchange_mappings: Dict[str, str]` - Exchange-specific formats
- `base_asset: str` - Base currency (e.g., "BTC")
- `quote_asset: str` - Quote currency (e.g., "USDT")
- `symbol_type: str` - "spot", "futures", "option"

**Example**:
```python
btc_mapping = SymbolMapping(
    internal_symbol="BTC/USDT",
    exchange_mappings={
        "binance_futures": "BTCUSDT",
        "hyperliquid": "BTC",
        "okx": "BTC-USDT-SWAP"
    },
    base_asset="BTC",
    quote_asset="USDT", 
    symbol_type="futures"
)
```

**Validation Rules**:
- `internal_symbol` must follow "BASE/QUOTE" format
- `exchange_mappings` must contain valid exchange names as keys
- `base_asset` and `quote_asset` must be valid currency codes

**Relationships**:
- **Used by** → ExchangeTrader implementations for symbol conversion
- **Configured in** → exchange.yaml configuration file
- **Validated by** → ConfigurationValidator

### RateLimit (Configuration Entity)
**Purpose**: Exchange-specific API rate limiting configuration

**Key Attributes**:
- `requests_per_minute: int` - General API requests limit
- `orders_per_minute: int` - Trading orders limit  
- `websocket_connections: int` - Maximum WebSocket connections
- `burst_allowance: int` - Temporary burst capacity
- `cooldown_period: int` - Cooldown after hitting limits (seconds)

**Validation Rules**:
- All limits must be positive integers
- `burst_allowance` ≤ `requests_per_minute`
- `cooldown_period` must be between 1 and 300 seconds

**Relationships**:
- **Part of** → ExchangeConfiguration
- **Used by** → CCXT rate limiting mechanisms
- **Enforced by** → ConnectionPoolManager

### TradingParameters (Configuration Entity)
**Purpose**: Exchange-specific trading rules and constraints

**Key Attributes**:
- `min_order_amounts: Dict[str, float]` - Minimum order sizes by symbol
- `max_leverage: Dict[str, int]` - Maximum leverage by symbol
- `supported_order_types: List[str]` - Available order types
- `precision_rules: Dict[str, Dict]` - Price/quantity precision by symbol
- `trading_fees: Dict[str, float]` - Fee rates by symbol

**Validation Rules**:
- `min_order_amounts` must have positive values
- `max_leverage` must have positive integer values
- `supported_order_types` must contain valid order type names
- Fee rates must be between 0 and 1 (0-100%)

**Relationships**:
- **Part of** → ExchangeConfiguration  
- **Used by** → Order validation and formatting
- **Updated from** → Exchange market info APIs

## Data Flow

### Trading Operation Flow
```
Agent Request → ExchangeTrader → OrderResult → Agent Response
     ↓               ↓              ↑
Configuration → Symbol Mapping → Raw Exchange Data
```

### Balance/Position Data Flow
```
Exchange APIs → ExchangeTrader → [Balance|Position] → Normalized Data
     ↓               ↓                    ↑
Raw Response → Data Normalization → Standard Format
```

### Configuration Loading Flow  
```
YAML Config → ConfigurationValidator → ExchangeConfiguration → ExchangeTrader
     ↓               ↓                        ↑
Environment → Credential Resolution → Validated Config
```

## Integration Points

### Existing System Integration
- **Agent Workflow**: Uses ExchangeTrader interface through existing `get_trader()` function
- **Position Service**: Receives enhanced Position objects with exchange information
- **History Service**: Records OrderResult data for trade history and analysis
- **Configuration System**: Extends existing settings.py with multi-exchange configuration

### Database Schema Changes (Minimal)
- **Orders Table**: Add `exchange` column to existing order records
- **Positions Table**: Add `exchange`, `position_id`, `liquidation_price` columns
- **Balance History**: Add `exchange`, `account_type` columns for multi-exchange tracking

### API Changes (Backward Compatible)
- **GET /balance**: Enhanced with exchange breakdown
- **GET /positions**: Enhanced with per-exchange position details
- **POST /orders**: Enhanced with exchange selection parameter
- **GET /exchanges**: New endpoint for exchange status and capabilities