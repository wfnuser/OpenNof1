"""
Binance Futures Trader implementation using CCXT
Handles real futures trading operations
"""
import logging
from typing import Dict, List, Optional, Any
import ccxt
from datetime import datetime

from trading.interface import ExchangeTrader, Position, Balance
from utils.logger import logger

logger = logging.getLogger("AlphaTransformer")


class BinanceFuturesTrader(ExchangeTrader):
    """Binance Futures交易器实现"""
    
    def __init__(self):
        try:
            # 创建CCXT Binance Futures实例
            from config.settings import config
            exchange_config = config.exchange.get_ccxt_config()
            self.exchange = ccxt.binance(exchange_config)
            
            # 设置默认类型为期货
            if not hasattr(self.exchange, 'defaultType') or self.exchange.defaultType != 'future':
                self.exchange.options['defaultType'] = 'future'
            
            logger.info(f"初始化Binance期货交易器，测试模式: {self.exchange.options.get('sandbox', False)}")
            
        except Exception as e:
            logger.error(f"初始化Binance期货交易器失败: {e}")
            raise
    
    async def get_balance(self) -> Balance:
        """获取合约账户余额"""
        balance = self.exchange.fetch_balance()
        
        total_usdt = balance['USDT']['total']
        free_usdt = balance['USDT']['free']
        
        positions = await self.get_positions()
        unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
        
        return Balance(
            total_balance=total_usdt,
            available_balance=free_usdt,
            margin_balance=total_usdt + unrealized_pnl,
            unrealized_pnl=unrealized_pnl,
            currency="USDT",
            timestamp=datetime.now()
        )
    
    async def get_positions(self) -> List[Position]:
        """获取所有持仓"""
        positions = self.exchange.fetch_positions()
        
        active_positions = []
        for pos in positions:
            if pos['contracts'] > 0:
                # 计算杠杆：1 / initialMarginPercentage
                initial_margin_pct = pos.get('initialMarginPercentage', 0.5)
                calculated_leverage = round(1 / initial_margin_pct) if initial_margin_pct > 0 else 1
                
                position = Position(
                    symbol=pos['symbol'],
                    side=pos['side'].upper(),
                    size=pos['contracts'],
                    entry_price=pos.get('entryPrice', 0.0),
                    mark_price=pos.get('markPrice', 0.0),
                    unrealized_pnl=pos.get('unrealizedPnl', 0.0),
                    percentage_pnl=pos.get('percentage', 0.0),
                    leverage=calculated_leverage,
                    margin=pos.get('initialMargin', 0.0),
                    timestamp=datetime.fromtimestamp(pos['timestamp'] / 1000) if pos.get('timestamp') else datetime.now()
                )
                active_positions.append(position)
        
        return active_positions
    
    async def open_long(self, symbol: str, quantity: float, leverage: int = 1, 
                       stop_loss_price: float = None, take_profit_price: float = None):
        """开多仓，可选择设置止损止盈"""
        logger.info(f"开多仓 {symbol} 数量: {quantity} 杠杆: {leverage}x")
        
        await self.set_leverage(symbol, leverage)
        
        # 1. 先开仓
        order = self.exchange.create_market_buy_order(symbol, quantity, params={'positionSide': 'LONG'})
        logger.info(f"开多仓订单执行: {order['id']}")
        
        
        # 2. 设置止损单（如果指定）
        if stop_loss_price:
            try:
                sl_order = self.exchange.create_order(
                    symbol, 'STOP_MARKET', 'sell', quantity, None, 
                    params={'stopPrice': stop_loss_price, 'positionSide': 'LONG'}
                )
                logger.info(f"止损单设置成功: {sl_order['id']} @ ${stop_loss_price}")
            except Exception as e:
                logger.error(f"设置止损单失败: {e}")
        
        # 3. 设置止盈单（如果指定）
        if take_profit_price:
            try:
                # 使用 limit 单作为止盈
                tp_order = self.exchange.create_order(
                    symbol, 'limit', 'sell', quantity, take_profit_price,
                    params={'positionSide': 'LONG'}
                )
                logger.info(f"止盈单设置成功: {tp_order['id']} @ ${take_profit_price}")
            except Exception as e:
                logger.error(f"设置止盈单失败: {e}")
        
        return order
    
    async def open_short(self, symbol: str, quantity: float, leverage: int = 1,
                        stop_loss_price: float = None, take_profit_price: float = None):
        """开空仓，可选择设置止损止盈"""
        logger.info(f"开空仓 {symbol} 数量: {quantity} 杠杆: {leverage}x")
        
        await self.set_leverage(symbol, leverage)
        
        # 1. 先开仓
        order = self.exchange.create_market_sell_order(symbol, quantity, params={'positionSide': 'SHORT'})
        logger.info(f"开空仓订单执行: {order['id']}")
        
        
        # 2. 设置止损单（如果指定）
        if stop_loss_price:
            try:
                sl_order = self.exchange.create_order(
                    symbol, 'STOP_MARKET', 'buy', quantity, None,
                    params={'stopPrice': stop_loss_price, 'positionSide': 'SHORT'}
                )
                logger.info(f"止损单设置成功: {sl_order['id']} @ ${stop_loss_price}")
            except Exception as e:
                logger.error(f"设置止损单失败: {e}")
        
        # 3. 设置止盈单（如果指定）
        if take_profit_price:
            try:
                # 使用 limit 单作为止盈
                tp_order = self.exchange.create_order(
                    symbol, 'limit', 'buy', quantity, take_profit_price,
                    params={'positionSide': 'SHORT'}
                )
                logger.info(f"止盈单设置成功: {tp_order['id']} @ ${take_profit_price}")
            except Exception as e:
                logger.error(f"设置止盈单失败: {e}")
        
        return order
    
    async def close_long(self, symbol: str, quantity: float = 0):
        """平多仓（quantity=0表示全部平仓）"""
        positions = await self.get_positions()
        long_position = None
        
        for pos in positions:
            # 标准化符号比较
            pos_symbol_normalized = pos.symbol.replace('/', '').replace(':USDT', '')
            symbol_normalized = symbol.replace('/', '').replace(':USDT', '')
            
            if pos_symbol_normalized == symbol_normalized and pos.side == "LONG":
                long_position = pos
                break
        
        if not long_position:
            raise ValueError(f"没有找到 {symbol} 的多头持仓")
        
        if quantity == 0:
            quantity = long_position.size
        
        if quantity > long_position.size:
            raise ValueError(f"平仓数量 {quantity} 超过持仓数量 {long_position.size}")
        
        logger.info(f"平多仓 {symbol} 数量: {quantity}")
        
        # 先取消相关挂单（止损止盈）
        await self.cancel_all_orders(symbol)
        
        # 执行平仓
        order = self.exchange.create_market_sell_order(symbol, quantity, params={'positionSide': 'LONG'})
        
        
        return order
    
    async def close_short(self, symbol: str, quantity: float = 0):
        """平空仓（quantity=0表示全部平仓）"""
        positions = await self.get_positions()
        short_position = None
        
        for pos in positions:
            # 标准化符号比较
            pos_symbol_normalized = pos.symbol.replace('/', '').replace(':USDT', '')
            symbol_normalized = symbol.replace('/', '').replace(':USDT', '')
            
            if pos_symbol_normalized == symbol_normalized and pos.side == "SHORT":
                short_position = pos
                break
        
        if not short_position:
            raise ValueError(f"没有找到 {symbol} 的空头持仓")
        
        if quantity == 0:
            quantity = short_position.size
        
        if quantity > short_position.size:
            raise ValueError(f"平仓数量 {quantity} 超过持仓数量 {short_position.size}")
        
        logger.info(f"平空仓 {symbol} 数量: {quantity}")
        
        # 先取消相关挂单（止损止盈）
        await self.cancel_all_orders(symbol)
        
        # 执行平仓
        order = self.exchange.create_market_buy_order(symbol, quantity, params={'positionSide': 'SHORT'})
        
        
        return order
    
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """设置杠杆"""
        try:
            self.exchange.set_leverage(leverage, symbol)
            logger.info(f"设置 {symbol} 杠杆为 {leverage}x")
            return True
        except Exception as e:
            logger.error(f"设置杠杆失败 {symbol}: {e}")
            return False
    
    async def set_margin_mode(self, symbol: str, is_cross_margin: bool) -> bool:
        """设置仓位模式"""
        try:
            margin_mode = 'cross' if is_cross_margin else 'isolated'
            self.exchange.set_margin_mode(margin_mode, symbol)
            logger.info(f"设置 {symbol} 保证金模式为 {margin_mode}")
            return True
        except Exception as e:
            logger.error(f"设置保证金模式失败 {symbol}: {e}")
            return False
    
    async def get_market_price(self, symbol: str) -> float:
        """获取市场价格"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"获取市场价格失败 {symbol}: {e}")
            return 0.0
    
    
    async def cancel_all_orders(self, symbol: str) -> bool:
        """取消该币种的所有挂单"""
        try:
            self.exchange.cancel_all_orders(symbol)
            logger.info(f"取消 {symbol} 所有挂单")
            return True
        except Exception as e:
            logger.error(f"取消挂单失败 {symbol}: {e}")
            return False
    
    def format_quantity(self, symbol: str, quantity: float) -> str:
        """格式化数量到正确的精度"""
        try:
            # 获取交易对信息
            markets = self.exchange.load_markets()
            if symbol in markets:
                precision = markets[symbol]['precision']['amount']
                return f"{quantity:.{precision}f}"
            return f"{quantity}"
        except Exception:
            return f"{quantity}"
    
    def get_exchange_name(self) -> str:
        """获取交易所名称"""
        return "binance_futures"
    
    


# 创建全局交易器实例
_trader_instance: Optional[BinanceFuturesTrader] = None


def get_trader() -> BinanceFuturesTrader:
    """获取全局交易器实例"""
    global _trader_instance
    if _trader_instance is None:
        _trader_instance = BinanceFuturesTrader()
    return _trader_instance