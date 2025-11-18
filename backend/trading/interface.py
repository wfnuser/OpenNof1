"""
Trading Interface - Exchange abstraction layer
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    side: str  # "LONG" or "SHORT"
    size: float  # 持仓数量
    entry_price: float  # 开仓价格
    mark_price: float  # 标记价格
    unrealized_pnl: float  # 未实现盈亏
    percentage_pnl: float  # 盈亏百分比
    leverage: float  # 杠杆倍数
    margin: float  # 占用保证金 (initial margin)
    timestamp: datetime


@dataclass
class Balance:
    """账户余额信息"""
    total_balance: float
    available_balance: float
    margin_balance: float
    unrealized_pnl: float
    currency: str
    timestamp: datetime


@dataclass
class OrderResult:
    """订单执行结果"""
    symbol: str
    order_id: str
    client_order_id: str
    side: str  # "BUY" or "SELL"
    order_type: str  # "MARKET", "LIMIT", etc.
    quantity: float
    price: Optional[float]  # 市价单可能为None
    executed_quantity: float
    executed_price: Optional[float]  # 可能为None
    status: str  # "FILLED", "PARTIALLY_FILLED", "CANCELLED", "FAILED"
    fees: float
    timestamp: datetime
    exchange: str
    raw_data: Optional[Dict[str, Any]] = None  # 原始交易所返回数据


class ExchangeTrader(ABC):
    """交易所交易器统一接口"""
    
    @abstractmethod
    async def get_balance(self) -> Balance:
        """获取账户余额"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """获取所有持仓"""
        pass
    
    @abstractmethod
    async def open_long(self, symbol: str, quantity: float, leverage: int = 1, 
                       stop_loss_price: float = None, take_profit_price: float = None):
        """开多仓，可选择设置止损止盈"""
        pass
    
    @abstractmethod
    async def open_short(self, symbol: str, quantity: float, leverage: int = 1,
                        stop_loss_price: float = None, take_profit_price: float = None):
        """开空仓，可选择设置止损止盈"""
        pass
    
    @abstractmethod
    async def close_long(self, symbol: str, quantity: float = 0):
        """平多仓（quantity=0表示全部平仓）"""
        pass
    
    @abstractmethod
    async def close_short(self, symbol: str, quantity: float = 0):
        """平空仓（quantity=0表示全部平仓）"""
        pass
    
    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """设置杠杆"""
        pass
    
    @abstractmethod
    async def set_margin_mode(self, symbol: str, is_cross_margin: bool) -> bool:
        """设置仓位模式 (true=全仓, false=逐仓)"""
        pass
    
    @abstractmethod
    async def get_market_price(self, symbol: str) -> float:
        """获取市场价格"""
        pass
    
    
    @abstractmethod
    async def cancel_all_orders(self, symbol: str) -> bool:
        """取消该币种的所有挂单"""
        pass
    
    @abstractmethod
    def format_quantity(self, symbol: str, quantity: float) -> str:
        """格式化数量到正确的精度"""
        pass
    
    @abstractmethod
    def get_exchange_name(self) -> str:
        """获取交易所名称"""
        pass


class TradingDecision:
    """交易决策"""
    
    # 期货交易动作类型
    OPEN_LONG = "OPEN_LONG"      # 开多仓
    OPEN_SHORT = "OPEN_SHORT"    # 开空仓
    CLOSE_LONG = "CLOSE_LONG"    # 平多仓
    CLOSE_SHORT = "CLOSE_SHORT"  # 平空仓
    HOLD = "HOLD"                # 持仓观望
    
    def __init__(self, action: str, symbol: str, quantity: float = None, 
                 reasoning: str = "", confidence: float = 0.0, 
                 leverage: int = 1, stop_loss: float = None, 
                 take_profit: float = None):
        self.action = action
        self.symbol = symbol
        self.quantity = quantity
        self.reasoning = reasoning
        self.confidence = confidence
        self.leverage = leverage
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.timestamp = datetime.now()
    
    def is_valid(self) -> bool:
        """验证决策是否有效"""
        valid_actions = [self.OPEN_LONG, self.OPEN_SHORT, self.CLOSE_LONG, self.CLOSE_SHORT, self.HOLD]
        return (self.action in valid_actions and 
                self.symbol and 
                self.confidence >= 0.0 and 
                self.confidence <= 1.0)
    
    def requires_execution(self) -> bool:
        """是否需要执行交易"""
        return self.action != self.HOLD
    
    def __str__(self) -> str:
        return f"TradingDecision({self.action} {self.symbol} qty={self.quantity} conf={self.confidence:.2f})"


class RiskManager:
    """风险管理器"""
    
    def __init__(self, max_position_size_percent: float = 0.1, 
                 max_daily_loss_percent: float = 0.05,
                 stop_loss_percent: float = 0.02):
        self.max_position_size_percent = max_position_size_percent
        self.max_daily_loss_percent = max_daily_loss_percent
        self.stop_loss_percent = stop_loss_percent
    
    def validate_decision(self, decision: TradingDecision, balance: Balance, 
                         positions: List[Position]) -> tuple[bool, str]:
        """验证交易决策是否符合风险控制"""
        
        # 杠杆检查已删除，使用配置中的默认杠杆
        
        # 检查仓位大小
        if decision.quantity:
            position_value = decision.quantity * (decision.stop_loss or 1)  # 简化计算
            if position_value > balance.total_balance * self.max_position_size_percent:
                return False, f"仓位大小超过 {self.max_position_size_percent * 100}% 限制"
        
        # 检查止损
        if decision.stop_loss is None and decision.action in [TradingDecision.OPEN_LONG, TradingDecision.OPEN_SHORT]:
            return False, "开仓必须设置止损"
        
        return True, "风险检查通过"