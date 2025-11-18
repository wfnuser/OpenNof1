# Research: CCXT Exchange Abstraction with Hyperliquid Support

**Feature**: Multi-exchange trading abstraction using CCXT
**Date**: 2025-11-18
**Status**: Research Complete

## Key Decisions

### 1. CCXT Integration Approach
**Decision**: Use CCXT library for unified exchange access with exchange-specific adapters
**Rationale**: 
- CCXT already supports both Binance and Hyperliquid with consistent API patterns
- Reduces custom integration code and maintenance burden
- Provides built-in rate limiting, error handling, and data normalization
- Active community and frequent updates for exchange API changes

**Implementation Pattern**:
```python
# Generic CCXT base class with exchange-specific extensions
class CCXTTrader(ExchangeTrader):
    # Common CCXT patterns
    
class BinanceFuturesTrader(CCXTTrader):
    # Binance-specific implementations
    
class HyperliquidTrader(CCXTTrader):  
    # Hyperliquid-specific implementations
```

### 2. Authentication Strategy
**Decision**: Support multiple authentication methods through unified configuration
**Rationale**:
- Binance supports API Key/Secret (legacy) and RSA Private Key (modern)
- Hyperliquid uses Wallet Address + Private Key pattern
- Future exchanges may have different authentication requirements
- Configuration-driven approach enables easy credential rotation

**Configuration Pattern**:
```yaml
exchanges:
  binance_futures:
    auth_type: "api_key"  # or "rsa_key"
    credentials:
      api_key: "${BINANCE_API_KEY}"
      secret: "${BINANCE_SECRET}"
  hyperliquid:
    auth_type: "wallet_key"
    credentials:
      wallet_address: "${HL_WALLET_ADDR}"
      private_key: "${HL_PRIVATE_KEY}"
```

### 3. Symbol Normalization Strategy  
**Decision**: Internal standard format with exchange-specific mapping
**Rationale**:
- Different exchanges use different symbol conventions (BTCUSDT vs BTC vs BTC-USD)
- Need consistent internal format for agent logic
- Exchange adapters handle format conversion transparently

**Mapping Pattern**:
```python
# Internal format: "BTC/USDT"
# Binance format: "BTCUSDT"  
# Hyperliquid format: "BTC"

class SymbolMapper:
    def to_exchange_format(self, symbol: str, exchange: str) -> str:
        # Convert "BTC/USDT" -> "BTCUSDT" for Binance
        # Convert "BTC/USDT" -> "BTC" for Hyperliquid
```

### 4. Backward Compatibility Approach
**Decision**: Incremental interface extraction with preserved legacy functions
**Rationale**:
- Existing agent code must continue working without changes
- Zero downtime migration required for production system
- Gradual enhancement allows testing at each step

**Migration Phases**:
1. **Phase 1**: Extract existing Binance code into enhanced interface (no breaking changes)
2. **Phase 2**: Add factory pattern for multi-exchange selection  
3. **Phase 3**: Add Hyperliquid implementation alongside Binance

### 5. Configuration Management Design
**Decision**: YAML-based configuration with environment variable integration
**Rationale**:
- Aligns with project's file-based configuration principle
- Environment variables for sensitive credentials
- Easy deployment across different environments
- Validation and testing before runtime

## Technical Research Findings

### CCXT Integration Patterns

**Authentication Mechanisms**:
- Binance: Transitioning from API Key/Secret to RSA Private Key for enhanced security
- Hyperliquid: Uses Ethereum wallet pattern (main wallet + API wallet for trading)
- Install `coincurve` library for 900x faster ECDSA signing performance (45ms → 0.05ms)

**Data Normalization Requirements**:
- Symbol mapping: Internal "BTC/USDT" → Binance "BTCUSDT" → Hyperliquid "BTC"
- Order types: Market/Limit/Stop variations across exchanges
- Precision handling: Different decimal place requirements for quantities and prices
- Time-in-force: GTC, IOC, FOK support varies by exchange

**Async/Await Best Practices**:
- Use `ccxt.async_support` for high-performance async operations
- Implement connection pooling and rate limiting (Binance: 1200 req/min, Hyperliquid: 600 req/min)
- Exponential backoff retry mechanisms with exchange-specific error handling
- Proper connection cleanup with async context managers

### Exchange Configuration Design

**Multi-Exchange YAML Structure**:
```yaml
# Global trading settings
trading:
  risk_management:
    max_position_size_percent: 10.0
    max_daily_loss_percent: 5.0
    stop_loss_percent: 2.0
  
  symbol_mapping:
    "BTC/USDT": 
      binance_futures: "BTCUSDT"
      hyperliquid: "BTC"

# Exchange-specific configurations  
exchanges:
  binance_futures:
    enabled: true
    auth_type: "api_key"
    testnet: true
    rate_limits:
      requests_per_minute: 1200
      orders_per_second: 10
      
  hyperliquid:
    enabled: true  
    auth_type: "wallet_key"
    testnet: false  # Hyperliquid has no testnet
    rate_limits:
      requests_per_minute: 600
      orders_per_second: 5
```

**Secure Credential Management**:
- Environment variable substitution: `"${BINANCE_API_KEY}"`
- HashiCorp Vault integration for enterprise deployments
- AES-256-GCM encryption for stored credentials
- Automatic credential validation and connection testing

### Interface Extraction Strategy

**Current BinanceFuturesTrader Analysis**:
- Uses CCXT Binance instance with futures-specific configuration
- Returns standardized dataclasses (Balance, Position) 
- Integrates with agent system via global `get_trader()` function
- Error logging follows consistent patterns

**Enhanced Interface Design**:
- Preserve all existing method signatures for backward compatibility
- Add standardized `OrderResult` return type for trading operations
- Include exchange-specific data in `raw_data` field for debugging
- Add new methods: `validate_symbol()`, `get_trading_fees()`, `normalize_symbol()`

**Migration Strategy**:
- **Week 1**: Interface extraction with zero functional changes
- **Week 2**: Add factory pattern and configuration enhancement
- **Week 3**: Implement Hyperliquid trader using new interface
- **Week 4**: Integration testing and production validation

## Implementation Recommendations

### 1. Start with Interface Enhancement
Enhance existing `ExchangeTrader` interface and refactor `BinanceFuturesTrader` to fully implement it while preserving all current functionality.

### 2. Add CCXT Base Class  
Create `CCXTTrader` abstract base class implementing common CCXT patterns for authentication, error handling, and data normalization.

### 3. Implement Factory Pattern
Add `trading/factory.py` with backward-compatible `get_trader()` function and new `get_exchange_trader(exchange_name)` function.

### 4. Configuration System Enhancement
Extend configuration system to support multiple exchanges while maintaining backward compatibility with current single-exchange setup.

### 5. Hyperliquid Implementation
Implement `HyperliquidTrader` extending `CCXTTrader` with Hyperliquid-specific authentication and symbol handling.

## Risk Mitigation

### Backward Compatibility Risks
- **Risk**: Breaking existing agent code  
- **Mitigation**: Preserve all method signatures and return types, maintain legacy `get_trader()` function

### Performance Risks  
- **Risk**: Added abstraction layer impacts trading latency
- **Mitigation**: Use async/await throughout, implement connection pooling, optimize CCXT usage

### Security Risks
- **Risk**: Multiple exchange credentials increase attack surface
- **Mitigation**: Encrypt credentials at rest, use environment variables, implement audit logging

### Configuration Complexity
- **Risk**: Multi-exchange configuration becomes difficult to manage
- **Mitigation**: Comprehensive validation, clear documentation, gradual migration approach

## Success Metrics

1. **Zero Regression**: All existing agent functionality works unchanged
2. **Performance Maintained**: Trading operations complete within current latency targets (<2 seconds)
3. **Easy Exchange Addition**: New CCXT-supported exchange can be added in <4 hours
4. **Configuration Simplicity**: Exchange switching through YAML configuration only
5. **Operational Reliability**: System maintains uptime when individual exchanges have issues