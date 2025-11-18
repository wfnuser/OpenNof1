"""
Exchange Trader Interface Contract
Defines the unified interface that all exchange implementations must follow
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    """Order status enumeration"""
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    PENDING = "PENDING"


class PositionSide(str, Enum):
    """Position side enumeration"""
    LONG = "LONG"
    SHORT = "SHORT"


class MarginType(str, Enum):
    """Margin type enumeration"""
    CROSS = "cross"
    ISOLATED = "isolated"


@dataclass
class OrderResult:
    """Standardized order execution result"""
    symbol: str
    order_id: str
    client_order_id: str = ""
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.MARKET
    quantity: float = 0.0
    price: Optional[float] = None
    executed_quantity: float = 0.0
    executed_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    fees: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    exchange: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate order result data"""
        if self.quantity < 0:
            raise ValueError("Quantity must be non-negative")
        if self.executed_quantity < 0:
            raise ValueError("Executed quantity must be non-negative")
        if self.executed_quantity > self.quantity:
            raise ValueError("Executed quantity cannot exceed requested quantity")


@dataclass
class Position:
    """Enhanced position information with multi-exchange support"""
    symbol: str
    side: PositionSide
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    percentage_pnl: float
    leverage: float
    margin: float
    timestamp: datetime
    
    # Enhanced fields for multi-exchange
    exchange: str = ""
    position_id: Optional[str] = None
    liquidation_price: Optional[float] = None
    margin_type: MarginType = MarginType.CROSS
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate position data"""
        if self.size <= 0:
            raise ValueError("Position size must be positive")
        if self.leverage <= 0:
            raise ValueError("Leverage must be positive")


@dataclass  
class Balance:
    """Enhanced balance information with multi-exchange support"""
    total_balance: float
    available_balance: float
    margin_balance: float
    unrealized_pnl: float
    currency: str
    timestamp: datetime
    
    # Enhanced fields for multi-exchange
    exchange: str = ""
    margin_used: float = 0.0
    maintenance_margin: float = 0.0
    can_trade: bool = True
    account_type: str = "futures"
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate balance data"""
        if self.total_balance < 0:
            raise ValueError("Total balance cannot be negative")
        if self.available_balance < 0:
            raise ValueError("Available balance cannot be negative")
        if self.available_balance > self.total_balance:
            raise ValueError("Available balance cannot exceed total balance")


@dataclass
class SymbolInfo:
    """Exchange symbol information"""
    symbol: str  # Internal format (e.g., "BTC/USDT")
    exchange_symbol: str  # Exchange-specific format (e.g., "BTCUSDT", "BTC")
    base_asset: str
    quote_asset: str
    active: bool
    symbol_type: str  # "spot", "futures", "option"
    min_order_amount: float
    max_leverage: int
    price_precision: int
    quantity_precision: int
    trading_fees: Dict[str, float]  # {"maker": 0.0002, "taker": 0.0004}


@dataclass
class TradingFees:
    """Trading fee information"""
    maker_fee: float  # Maker fee rate (0.0002 = 0.02%)
    taker_fee: float  # Taker fee rate (0.0004 = 0.04%)  
    currency: str = "USDT"  # Fee currency


class ExchangeTrader(ABC):
    """
    Unified exchange trader interface.
    All exchange implementations must implement this interface.
    """

    # Core data retrieval methods
    @abstractmethod
    async def get_balance(self) -> Balance:
        """
        Get account balance information.
        
        Returns:
            Balance: Account balance with exchange information
            
        Raises:
            ConnectionError: If unable to connect to exchange
            AuthenticationError: If credentials are invalid
        """
        pass

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """
        Get all active positions.
        
        Returns:
            List[Position]: List of active positions
            
        Raises:
            ConnectionError: If unable to connect to exchange
        """
        pass

    # Trading operations with standardized returns
    @abstractmethod
    async def open_long(
        self,
        symbol: str,
        quantity: float,
        leverage: int = 1,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> OrderResult:
        """
        Open a long position.
        
        Args:
            symbol: Trading pair symbol (internal format)
            quantity: Order quantity
            leverage: Leverage multiplier
            stop_loss_price: Optional stop loss price
            take_profit_price: Optional take profit price
            
        Returns:
            OrderResult: Standardized order execution result
            
        Raises:
            ValueError: If parameters are invalid
            InsufficientFundsError: If insufficient balance
            TradingError: If order execution fails
        """
        pass

    @abstractmethod
    async def open_short(
        self,
        symbol: str,
        quantity: float,
        leverage: int = 1,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> OrderResult:
        """
        Open a short position.
        
        Args:
            symbol: Trading pair symbol (internal format)
            quantity: Order quantity
            leverage: Leverage multiplier
            stop_loss_price: Optional stop loss price
            take_profit_price: Optional take profit price
            
        Returns:
            OrderResult: Standardized order execution result
            
        Raises:
            ValueError: If parameters are invalid
            InsufficientFundsError: If insufficient balance
            TradingError: If order execution fails
        """
        pass

    @abstractmethod
    async def close_long(self, symbol: str, quantity: float = 0) -> OrderResult:
        """
        Close a long position.
        
        Args:
            symbol: Trading pair symbol (internal format)
            quantity: Quantity to close (0 = close all)
            
        Returns:
            OrderResult: Standardized order execution result
            
        Raises:
            ValueError: If parameters are invalid
            PositionNotFoundError: If no position to close
            TradingError: If order execution fails
        """
        pass

    @abstractmethod
    async def close_short(self, symbol: str, quantity: float = 0) -> OrderResult:
        """
        Close a short position.
        
        Args:
            symbol: Trading pair symbol (internal format)
            quantity: Quantity to close (0 = close all)
            
        Returns:
            OrderResult: Standardized order execution result
            
        Raises:
            ValueError: If parameters are invalid
            PositionNotFoundError: If no position to close
            TradingError: If order execution fails
        """
        pass

    # Configuration methods
    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for a symbol.
        
        Args:
            symbol: Trading pair symbol (internal format)
            leverage: Leverage multiplier
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If leverage is invalid
            ConfigurationError: If setting fails
        """
        pass

    @abstractmethod
    async def set_margin_mode(self, symbol: str, is_cross_margin: bool) -> bool:
        """
        Set margin mode for a symbol.
        
        Args:
            symbol: Trading pair symbol (internal format)
            is_cross_margin: True for cross margin, False for isolated
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If parameters are invalid
            ConfigurationError: If setting fails
        """
        pass

    # Market data methods
    @abstractmethod
    async def get_market_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading pair symbol (internal format)
            
        Returns:
            float: Current market price
            
        Raises:
            SymbolNotFoundError: If symbol is not available
            ConnectionError: If unable to fetch price
        """
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get ticker information for a symbol.
        
        Args:
            symbol: Trading pair symbol (internal format)
            
        Returns:
            Dict[str, Any]: Ticker data including price, volume, etc.
            
        Raises:
            SymbolNotFoundError: If symbol is not available
        """
        pass

    # Order management
    @abstractmethod
    async def cancel_all_orders(self, symbol: str) -> bool:
        """
        Cancel all open orders for a symbol.
        
        Args:
            symbol: Trading pair symbol (internal format)
            
        Returns:
            bool: True if successful
            
        Raises:
            ConnectionError: If unable to cancel orders
        """
        pass

    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel a specific order.
        
        Args:
            symbol: Trading pair symbol (internal format)
            order_id: Exchange-specific order ID
            
        Returns:
            bool: True if successful
            
        Raises:
            OrderNotFoundError: If order doesn't exist
            ConnectionError: If unable to cancel order
        """
        pass

    # Utility methods
    @abstractmethod
    def format_quantity(self, symbol: str, quantity: float) -> str:
        """
        Format quantity to correct precision for this exchange.
        
        Args:
            symbol: Trading pair symbol (internal format)
            quantity: Raw quantity value
            
        Returns:
            str: Formatted quantity string
        """
        pass

    @abstractmethod
    def format_price(self, symbol: str, price: float) -> str:
        """
        Format price to correct precision for this exchange.
        
        Args:
            symbol: Trading pair symbol (internal format)
            price: Raw price value
            
        Returns:
            str: Formatted price string
        """
        pass

    @abstractmethod
    def get_exchange_name(self) -> str:
        """
        Get exchange identifier.
        
        Returns:
            str: Exchange name (e.g., "binance_futures", "hyperliquid")
        """
        pass

    @abstractmethod
    def get_trading_fees(self, symbol: str) -> TradingFees:
        """
        Get trading fees for a symbol.
        
        Args:
            symbol: Trading pair symbol (internal format)
            
        Returns:
            TradingFees: Fee information for this symbol
            
        Raises:
            SymbolNotFoundError: If symbol is not available
        """
        pass

    # Enhanced validation and utility methods
    @abstractmethod
    async def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is tradable on this exchange.
        
        Args:
            symbol: Trading pair symbol (internal format)
            
        Returns:
            bool: True if symbol is tradable
        """
        pass

    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """
        Convert internal symbol format to exchange-specific format.
        
        Args:
            symbol: Symbol in internal format (e.g., "BTC/USDT")
            
        Returns:
            str: Symbol in exchange format (e.g., "BTCUSDT", "BTC")
        """
        pass

    @abstractmethod
    def denormalize_symbol(self, exchange_symbol: str) -> str:
        """
        Convert exchange-specific symbol format to internal format.
        
        Args:
            exchange_symbol: Symbol in exchange format (e.g., "BTCUSDT")
            
        Returns:
            str: Symbol in internal format (e.g., "BTC/USDT")
        """
        pass

    @abstractmethod
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """
        Get detailed symbol information.
        
        Args:
            symbol: Trading pair symbol (internal format)
            
        Returns:
            SymbolInfo: Detailed symbol information
            
        Raises:
            SymbolNotFoundError: If symbol is not available
        """
        pass

    @abstractmethod
    async def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange-specific information and limits.
        
        Returns:
            Dict[str, Any]: Exchange information including:
                - rate_limits: API rate limiting information
                - trading_rules: General trading rules
                - supported_order_types: Available order types
                - supported_symbols: List of tradable symbols
        """
        pass

    # Connection management
    async def connect(self) -> bool:
        """
        Establish connection to the exchange.
        Called automatically by factory, but can be called manually.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            AuthenticationError: If credentials are invalid
            ConnectionError: If unable to connect
        """
        # Default implementation - exchanges can override
        try:
            await self.get_exchange_info()
            return True
        except Exception:
            return False

    async def disconnect(self) -> None:
        """
        Close connection to the exchange.
        Should be called during application shutdown.
        """
        # Default implementation - exchanges can override
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on exchange connection.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        # Default implementation - exchanges can override
        try:
            start_time = datetime.now()
            await self.get_exchange_info()
            end_time = datetime.now()
            
            return {
                "status": "healthy",
                "exchange": self.get_exchange_name(),
                "response_time_ms": (end_time - start_time).total_seconds() * 1000,
                "timestamp": datetime.now()
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "exchange": self.get_exchange_name(),
                "error": str(e),
                "timestamp": datetime.now()
            }


# Custom exceptions for better error handling
class ExchangeError(Exception):
    """Base exception for exchange-related errors"""
    pass


class AuthenticationError(ExchangeError):
    """Authentication failed"""
    pass


class InsufficientFundsError(ExchangeError):
    """Insufficient funds for operation"""
    pass


class SymbolNotFoundError(ExchangeError):
    """Symbol not found or not tradable"""
    pass


class PositionNotFoundError(ExchangeError):
    """Position not found"""
    pass


class OrderNotFoundError(ExchangeError):
    """Order not found"""
    pass


class TradingError(ExchangeError):
    """General trading operation error"""
    pass


class ConfigurationError(ExchangeError):
    """Configuration setting error"""
    pass