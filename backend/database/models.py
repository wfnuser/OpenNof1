"""
Database models for trading system - Simplified design
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, text
from sqlalchemy.sql import func
import uuid

from database.database import Base


class TradingAnalysis(Base):
    """一次完整的AI分析决策记录"""
    __tablename__ = "trading_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(36), nullable=False, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)
    
    # AI分析结果
    overall_summary = Column(Text, nullable=True)  # AI的整体市场分析
    symbol_decisions = Column(JSON, nullable=False)  # 所有交易对的决策和执行结果
    duration_ms = Column(Float, nullable=True)  # 分析和执行总耗时
    
    # 元数据
    model_name = Column(String(50), nullable=False)  # AI模型名称
    error = Column(Text, nullable=True)  # 错误信息（如果有）
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    def __repr__(self):
        return (f"TradingAnalysis(id={self.id}, analysis_id={self.analysis_id}, "
                f"symbols={len(self.symbol_decisions or {})})")


class BalanceSnapshot(Base):
    """账户余额快照记录"""
    __tablename__ = "balance_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)
    total_balance = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=False)
    margin_balance = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default="USDT")
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    def __repr__(self):
        return (f"BalanceSnapshot(id={self.id}, timestamp={self.timestamp}, "
                f"total={self.total_balance}, unrealized_pnl={self.unrealized_pnl})")


class OrderRecord(Base):
    """订单记录"""
    __tablename__ = "order_records"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), nullable=False, unique=True, index=True)  # 交易所订单ID
    analysis_id = Column(String(36), nullable=True, index=True)  # 关联的分析ID
    
    # 订单基本信息
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY/SELL
    type = Column(String(20), nullable=False)  # MARKET/LIMIT/STOP_MARKET等
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    
    # 执行信息
    filled = Column(Float, nullable=False, default=0.0)
    remaining = Column(Float, nullable=False, default=0.0)
    average_price = Column(Float, nullable=True)
    cost = Column(Float, nullable=False, default=0.0)
    fee = Column(Float, nullable=False, default=0.0)
    fee_currency = Column(String(10), nullable=True)
    
    # 状态和时间
    status = Column(String(20), nullable=False)  # open/closed/canceled
    order_type_detail = Column(String(50), nullable=True)  # 订单详细类型：open_long/close_short等
    
    created_time = Column(DateTime, nullable=False)  # 订单创建时间
    updated_time = Column(DateTime, nullable=True)   # 订单更新时间
    filled_time = Column(DateTime, nullable=True)    # 订单成交时间
    
    # 原始数据
    raw_data = Column(JSON, nullable=True)  # 交易所原始返回数据
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    def __repr__(self):
        return (f"OrderRecord(id={self.id}, order_id={self.order_id}, "
                f"symbol={self.symbol}, side={self.side}, status={self.status})")


class TradeRecord(Base):
    """交易成交记录"""
    __tablename__ = "trade_records"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String(100), nullable=False, unique=True, index=True)  # 交易所成交ID
    order_id = Column(String(100), nullable=False, index=True)  # 关联订单ID
    analysis_id = Column(String(36), nullable=True, index=True)  # 关联的分析ID
    
    # 交易信息
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy/sell
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)  # amount * price
    
    # 手续费
    fee_cost = Column(Float, nullable=False, default=0.0)
    fee_currency = Column(String(10), nullable=True)
    
    # 时间
    trade_time = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # 原始数据
    raw_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return (f"TradeRecord(id={self.id}, trade_id={self.trade_id}, "
                f"symbol={self.symbol}, amount={self.amount}, price={self.price})")


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"SystemConfig(key={self.key}, value={self.value})"


