# Implementation Plan: CCXT Exchange Abstraction with Hyperliquid Support

**Branch**: `003-ccxt-exchange-abstraction` | **Date**: 2025-11-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-ccxt-exchange-abstraction/spec.md`

**Note**: User guidance: Keep tasks simple, introduce interfaces first to ensure existing code works, then add Hyperliquid.

## Summary

Create a unified exchange abstraction layer using CCXT to support multiple trading exchanges (initially Binance + Hyperliquid) with minimal disruption to existing code. The approach prioritizes incremental implementation: first extract existing Binance functionality into a generic interface, then add Hyperliquid support.

## Technical Context

**Language/Version**: Python 3.11+ (established in backend)  
**Primary Dependencies**: CCXT library, existing FastAPI/LangChain stack  
**Storage**: Existing SQLite database with minimal schema changes  
**Testing**: pytest (current testing framework)  
**Target Platform**: Linux server (current deployment target)
**Project Type**: Backend trading system enhancement  
**Performance Goals**: <2 seconds for trading operations, maintain existing latency  
**Constraints**: Zero downtime migration, backward compatibility required  
**Scale/Scope**: Support 2-5 exchanges initially, extensible to any CCXT-supported exchange

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Agent-First Architecture**: Exchange abstraction enables AI agents to trade on multiple venues through unified interface  
✅ **Python AI Ecosystem Integration**: Uses CCXT (Python-native) with existing LangGraph/FastAPI stack  
✅ **File-Based Configuration**: Exchange credentials and settings managed via YAML configuration  
✅ **User Profit-First Design**: Multi-exchange support increases liquidity options and reduces counterparty risk  
✅ **Extensible Tools & MCP Future-Proofing**: Interface-based design enables future exchange integrations  
✅ **SQLite Simplicity**: Minimal database changes, leverage existing SQLite infrastructure  
✅ **Multi-Exchange Abstraction**: Core requirement directly addresses this constitutional principle  
✅ **Risk Management Requirements**: Maintains existing risk controls across all exchanges  

**Status**: All constitutional requirements satisfied ✅

## Project Structure

### Documentation (this feature)

```text
specs/003-ccxt-exchange-abstraction/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── trading/
│   ├── interface.py         # Enhanced ExchangeTrader interface
│   ├── binance_futures.py   # Refactored Binance implementation
│   ├── ccxt_trader.py       # New: Generic CCXT-based trader
│   ├── hyperliquid_trader.py # New: Hyperliquid-specific implementation
│   └── factory.py           # New: Exchange trader factory
├── config/
│   ├── settings.py          # Enhanced with exchange configuration
│   └── exchange.yaml        # New: Exchange-specific settings
└── tests/
    ├── test_exchange_interface.py
    ├── test_binance_integration.py
    └── test_hyperliquid_integration.py
```

**Structure Decision**: Enhance existing backend/trading/ directory with minimal structural changes to preserve working functionality while adding new abstraction components.

## Phase 0: Research & Technical Foundation

### Research Tasks

1. **CCXT Integration Patterns**
   - Document CCXT authentication mechanisms for Binance vs Hyperliquid
   - Identify data normalization requirements between exchanges
   - Research CCXT async/await best practices for Python

2. **Exchange Configuration Design**  
   - Design YAML configuration schema for multi-exchange credentials
   - Research secure credential management approaches
   - Document exchange-specific parameter mapping (symbols, order types)

3. **Interface Extraction Strategy**
   - Analyze existing BinanceFuturesTrader methods for common patterns
   - Document interface method signatures that work across exchanges
   - Research backward compatibility approaches for existing code

**Expected Outcomes**: Clear technical approach for interface extraction and CCXT integration patterns.

## Phase 1: Design & Implementation Strategy

### Stage 1: Interface Extraction (Priority 1 - Keep existing code working)

**Goal**: Extract existing Binance functionality into a generic interface without breaking current operations.

#### Task 1.1: Enhance ExchangeTrader Interface
- Review current `trading/interface.py` ExchangeTrader abstract class
- Add missing methods needed for CCXT integration  
- Ensure interface covers all Binance functionality currently used by agents

#### Task 1.2: Refactor BinanceFuturesTrader
- Modify existing `binance_futures.py` to fully implement enhanced interface
- Ensure zero functional changes to existing trading logic
- Add comprehensive test coverage to validate behavior preservation

#### Task 1.3: Create Exchange Factory
- Implement `trading/factory.py` to instantiate exchange traders based on configuration
- Support backward compatibility with existing Binance-only configuration
- Enable dynamic exchange selection via configuration

### Stage 2: CCXT Foundation (Priority 2 - Enable new exchanges)

#### Task 2.1: Generic CCXT Trader
- Create `trading/ccxt_trader.py` as base class for CCXT-based exchanges
- Implement common CCXT patterns (authentication, data normalization, error handling)
- Provide abstract methods for exchange-specific customization

#### Task 2.2: Configuration System Enhancement
- Enhance `config/settings.py` to support multiple exchange configurations
- Create `config/exchange.yaml` template for exchange-specific settings
- Implement configuration validation and exchange capability detection

### Stage 3: Hyperliquid Integration (Priority 3 - Add second exchange)

#### Task 3.1: Hyperliquid Trader Implementation
- Create `trading/hyperliquid_trader.py` extending CCXTTrader
- Implement Hyperliquid-specific authentication and API patterns
- Handle Hyperliquid symbol mapping and order type differences

#### Task 3.2: Integration Testing  
- Create comprehensive test suite for cross-exchange functionality
- Validate identical trading strategies execute consistently across exchanges
- Test exchange failover and error isolation scenarios

## Complexity Tracking

*No constitutional violations - implementation follows established patterns with incremental enhancement approach.*