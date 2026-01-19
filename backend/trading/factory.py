"""
Trading Exchange Factory - 统一交易所实例创建
"""
from typing import Dict, Optional

from trading.interface import ExchangeTrader
from trading.binance_futures import BinanceFuturesTrader
from trading.hyperliquid_trader import HyperliquidTrader


_TRADER_CACHE: Dict[str, ExchangeTrader] = {}


def get_exchange_trader(exchange_name: Optional[str] = None) -> ExchangeTrader:
    """
    获取交易所交易器实例
    
    Args:
        exchange_name: 交易所名称，默认为 None（使用币安）
        
    Returns:
        ExchangeTrader: 统一的交易器接口实例
        
    Raises:
        ValueError: 不支持的交易所名称
    """
    from config.settings import config

    target_name = exchange_name or config.exchange.name

    normalized_name = _normalize_exchange_name(target_name)

    if normalized_name not in _TRADER_CACHE:
        if normalized_name == "binance_futures":
            if config.get_exchange_entry("binance_futures") is None:
                raise ValueError("配置中未提供 Binance Futures 交易所")
            _TRADER_CACHE[normalized_name] = BinanceFuturesTrader()
        elif normalized_name == "hyperliquid":
            if config.get_exchange_entry("hyperliquid") is None:
                raise ValueError("配置中未启用 Hyperliquid 交易所")
            _TRADER_CACHE[normalized_name] = HyperliquidTrader()
        else:
            raise ValueError(f"不支持的交易所: {exchange_name}")

    return _TRADER_CACHE[normalized_name]


# 保持向后兼容的快捷函数
def get_trader() -> ExchangeTrader:
    """获取默认交易器（币安），保持向后兼容"""
    return get_exchange_trader("binance")


def _normalize_exchange_name(name: str) -> str:
    normalized = (name or "binance_futures").lower()
    if normalized in {"binance", "binance_futures"}:
        return "binance_futures"
    if normalized in {"hyperliquid", "hl"}:
        return "hyperliquid"
    return normalized
