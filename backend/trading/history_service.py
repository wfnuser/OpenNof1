"""
Trading History Service - 管理余额和订单历史数据
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
import json

from database.database import get_session_maker
from database.models import BalanceSnapshot, OrderRecord, TradeRecord, SystemConfig
from trading.binance_futures import get_trader
from utils.logger import logger

logger = logging.getLogger("AlphaTransformer")


class TradingHistoryService:
    """交易历史数据管理服务"""
    
    def __init__(self):
        self.trader = get_trader()
    
    async def initialize_if_needed(self):
        """检查并初始化系统（在服务启动时调用）"""
        init_time = await self.get_init_timestamp()
        if not init_time:
            logger.info("系统首次启动，开始自动初始化历史数据系统...")
            await self.auto_initialize()
        else:
            logger.info(f"系统已初始化，初始化时间: {init_time}")
    
    async def auto_initialize(self):
        """自动初始化系统（首次启动时调用）"""
        try:
            # 设置初始化时间为当前时间
            init_time = await self.set_init_timestamp()
            
            # 全量同步历史数据
            logger.info("开始全量同步历史数据...")
            order_count = await self.sync_historical_orders(full_sync=True)
            trade_count = await self.sync_historical_trades(full_sync=True)
            
            # 记录初始余额快照
            await self.record_balance_snapshot()
            
            logger.info(f"系统自动初始化完成: 同步{order_count}个订单, {trade_count}个交易")
            
        except Exception as e:
            logger.error(f"自动初始化失败: {e}")
            raise
    
    async def reset_system(self, new_init_time: Optional[datetime] = None):
        """重置整个系统（清空所有历史数据并重新初始化）"""
        try:
            logger.info("开始重置系统...")
            
            async with get_session_maker()() as session:
                # 清空所有历史数据表
                await session.execute(text("DELETE FROM balance_snapshots"))
                await session.execute(text("DELETE FROM order_records"))
                await session.execute(text("DELETE FROM trade_records"))
                await session.commit()
                
            logger.info("历史数据清空完成")
            
            # 重新设置初始化时间
            if new_init_time is None:
                new_init_time = datetime.now(timezone.utc)
            
            await self.set_init_timestamp(new_init_time)
            
            # 重新同步数据
            order_count = await self.sync_historical_orders(full_sync=True)
            trade_count = await self.sync_historical_trades(full_sync=True)
            
            # 记录新的余额快照
            await self.record_balance_snapshot()
            
            logger.info(f"系统重置完成: 初始化时间={new_init_time}, 同步{order_count}个订单, {trade_count}个交易")
            
            return {
                "success": True,
                "message": "系统重置完成",
                "init_time": new_init_time.isoformat(),
                "synced_orders": order_count,
                "synced_trades": trade_count
            }
            
        except Exception as e:
            logger.error(f"系统重置失败: {e}")
            raise
    
    async def get_init_timestamp(self) -> Optional[datetime]:
        """获取系统初始化时间"""
        async with get_session_maker()() as session:
            stmt = select(SystemConfig).where(SystemConfig.key == "system_init_time")
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if config:
                return datetime.fromisoformat(config.value)
            return None
    
    async def set_init_timestamp(self, init_time: Optional[datetime] = None) -> datetime:
        """设置系统初始化时间"""
        if init_time is None:
            init_time = datetime.now(timezone.utc)
        
        async with get_session_maker()() as session:
            # 查找现有配置
            stmt = select(SystemConfig).where(SystemConfig.key == "system_init_time")
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if config:
                config.value = init_time.isoformat()
                config.updated_at = datetime.now(timezone.utc)
            else:
                config = SystemConfig(
                    key="system_init_time",
                    value=init_time.isoformat(),
                    description="系统初始化时间，只记录此时间后的数据"
                )
                session.add(config)
            
            await session.commit()
            logger.info(f"设置系统初始化时间: {init_time}")
            return init_time
    
    async def record_balance_snapshot(self):
        """记录当前余额快照"""
        try:
            # 获取当前余额
            balance = await self.trader.get_balance()
            
            async with get_session_maker()() as session:
                snapshot = BalanceSnapshot(
                    timestamp=balance.timestamp,
                    total_balance=balance.total_balance,
                    available_balance=balance.available_balance,
                    margin_balance=balance.margin_balance,
                    unrealized_pnl=balance.unrealized_pnl,
                    currency=balance.currency
                )
                session.add(snapshot)
                await session.commit()
                
                logger.info(f"记录余额快照: 总计={balance.total_balance:.2f}, "
                           f"未实现盈亏={balance.unrealized_pnl:.2f}")
                
        except Exception as e:
            logger.error(f"记录余额快照失败: {e}")
            raise
    
    async def sync_recent_orders(self, hours: int = 24, symbols: Optional[List[str]] = None) -> int:
        """同步最近的订单数据（更高效）"""
        if symbols is None:
            from config.settings import config
            symbols = config.agent.symbols
        
        # 只同步最近N小时的数据
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        since_ms = int(since_time.timestamp() * 1000)
        total_orders = 0
        
        for symbol in symbols:
            try:
                logger.debug(f"同步 {symbol} 最近 {hours}h 的订单...")
                orders = self.trader.exchange.fetch_orders(symbol, since=since_ms)
                
                async with get_session_maker()() as session:
                    for order_data in orders:
                        await self._save_order_record(session, order_data)
                    await session.commit()
                
                total_orders += len(orders)
                logger.debug(f"同步 {symbol} 订单: {len(orders)} 条")
                
                # 避免API限制
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"同步 {symbol} 订单失败: {e}")
        
        if total_orders > 0:
            logger.info(f"同步最近 {hours}h 订单: {total_orders} 条")
        return total_orders
    
    async def sync_historical_orders(self, symbols: Optional[List[str]] = None, full_sync: bool = False) -> int:
        """同步历史订单数据"""
        init_time = await self.get_init_timestamp()
        if not init_time:
            logger.warning("系统未设置初始化时间，无法同步历史订单")
            return 0
        
        if symbols is None:
            from config.settings import config
            symbols = config.agent.symbols
        
        # 如果不是全量同步，只同步最近的数据
        if not full_sync:
            return await self.sync_recent_orders(24, symbols)
        
        since_ms = int(init_time.timestamp() * 1000)
        total_orders = 0
        
        for symbol in symbols:
            try:
                logger.info(f"全量同步 {symbol} 的历史订单...")
                orders = self.trader.exchange.fetch_orders(symbol, since=since_ms)
                
                async with get_session_maker()() as session:
                    for order_data in orders:
                        await self._save_order_record(session, order_data)
                    await session.commit()
                
                total_orders += len(orders)
                logger.info(f"同步 {symbol} 订单: {len(orders)} 条")
                
                # 避免API限制
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"同步 {symbol} 订单失败: {e}")
        
        logger.info(f"总共同步订单: {total_orders} 条")
        return total_orders
    
    async def sync_recent_trades(self, hours: int = 24, symbols: Optional[List[str]] = None) -> int:
        """同步最近的交易数据（更高效）"""
        if symbols is None:
            from config.settings import config
            symbols = config.agent.symbols
        
        # 只同步最近N小时的数据
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        since_ms = int(since_time.timestamp() * 1000)
        total_trades = 0
        
        for symbol in symbols:
            try:
                logger.debug(f"同步 {symbol} 最近 {hours}h 的交易...")
                trades = self.trader.exchange.fetch_my_trades(symbol, since=since_ms)
                
                async with get_session_maker()() as session:
                    for trade_data in trades:
                        await self._save_trade_record(session, trade_data)
                    await session.commit()
                
                total_trades += len(trades)
                logger.debug(f"同步 {symbol} 交易: {len(trades)} 条")
                
                # 避免API限制
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"同步 {symbol} 交易失败: {e}")
        
        if total_trades > 0:
            logger.info(f"同步最近 {hours}h 交易: {total_trades} 条")
        return total_trades
    
    async def sync_historical_trades(self, symbols: Optional[List[str]] = None, full_sync: bool = False) -> int:
        """同步历史交易数据"""
        init_time = await self.get_init_timestamp()
        if not init_time:
            logger.warning("系统未设置初始化时间，无法同步历史交易")
            return 0
        
        if symbols is None:
            from config.settings import config
            symbols = config.agent.symbols
        
        # 如果不是全量同步，只同步最近的数据
        if not full_sync:
            return await self.sync_recent_trades(24, symbols)
        
        since_ms = int(init_time.timestamp() * 1000)
        total_trades = 0
        
        for symbol in symbols:
            try:
                logger.info(f"全量同步 {symbol} 的历史交易...")
                trades = self.trader.exchange.fetch_my_trades(symbol, since=since_ms)
                
                async with get_session_maker()() as session:
                    for trade_data in trades:
                        await self._save_trade_record(session, trade_data)
                    await session.commit()
                
                total_trades += len(trades)
                logger.info(f"同步 {symbol} 交易: {len(trades)} 条")
                
                # 避免API限制
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"同步 {symbol} 交易失败: {e}")
        
        logger.info(f"总共同步交易: {total_trades} 条")
        return total_trades
    
    async def _save_order_record(self, session: AsyncSession, order_data: Dict[str, Any]):
        """保存订单记录到数据库"""
        try:
            # 检查是否已存在
            stmt = select(OrderRecord).where(OrderRecord.order_id == order_data['id'])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新现有记录
                existing.filled = order_data.get('filled', 0.0)
                existing.remaining = order_data.get('remaining', 0.0)
                existing.average_price = order_data.get('average', None)
                existing.cost = order_data.get('cost', 0.0)
                existing.fee = order_data.get('fee', {}).get('cost', 0.0) if order_data.get('fee') else 0.0
                existing.fee_currency = order_data.get('fee', {}).get('currency', None) if order_data.get('fee') else None
                existing.status = order_data.get('status', 'unknown')
                existing.updated_time = datetime.fromtimestamp(order_data['lastTradeTimestamp'] / 1000, timezone.utc) if order_data.get('lastTradeTimestamp') else None
                existing.filled_time = datetime.fromtimestamp(order_data['lastTradeTimestamp'] / 1000, timezone.utc) if order_data.get('lastTradeTimestamp') and order_data.get('status') == 'closed' else None
                existing.raw_data = order_data
            else:
                # 创建新记录
                order_record = OrderRecord(
                    order_id=order_data['id'],
                    symbol=order_data['symbol'],
                    side=order_data['side'].upper(),
                    type=order_data['type'].upper(),
                    amount=order_data.get('amount', 0.0),
                    price=order_data.get('price', None),
                    filled=order_data.get('filled', 0.0),
                    remaining=order_data.get('remaining', 0.0),
                    average_price=order_data.get('average', None),
                    cost=order_data.get('cost', 0.0),
                    fee=order_data.get('fee', {}).get('cost', 0.0) if order_data.get('fee') else 0.0,
                    fee_currency=order_data.get('fee', {}).get('currency', None) if order_data.get('fee') else None,
                    status=order_data.get('status', 'unknown'),
                    created_time=datetime.fromtimestamp(order_data['timestamp'] / 1000, timezone.utc),
                    updated_time=datetime.fromtimestamp(order_data['lastTradeTimestamp'] / 1000, timezone.utc) if order_data.get('lastTradeTimestamp') else None,
                    filled_time=datetime.fromtimestamp(order_data['lastTradeTimestamp'] / 1000, timezone.utc) if order_data.get('lastTradeTimestamp') and order_data.get('status') == 'closed' else None,
                    raw_data=order_data
                )
                session.add(order_record)
                
        except Exception as e:
            logger.error(f"保存订单记录失败: {e}")
    
    async def _save_trade_record(self, session: AsyncSession, trade_data: Dict[str, Any]):
        """保存交易记录到数据库"""
        try:
            # 检查是否已存在
            stmt = select(TradeRecord).where(TradeRecord.trade_id == trade_data['id'])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                return  # 交易记录不应该变化，如果已存在就跳过
            
            trade_record = TradeRecord(
                trade_id=trade_data['id'],
                order_id=trade_data['order'],
                symbol=trade_data['symbol'],
                side=trade_data['side'],
                amount=trade_data['amount'],
                price=trade_data['price'],
                cost=trade_data['cost'],
                fee_cost=trade_data.get('fee', {}).get('cost', 0.0) if trade_data.get('fee') else 0.0,
                fee_currency=trade_data.get('fee', {}).get('currency', None) if trade_data.get('fee') else None,
                trade_time=datetime.fromtimestamp(trade_data['timestamp'] / 1000, timezone.utc),
                raw_data=trade_data
            )
            session.add(trade_record)
            
        except Exception as e:
            logger.error(f"保存交易记录失败: {e}")
    
    
    async def get_balance_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取余额历史"""
        async with get_session_maker()() as session:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            stmt = select(BalanceSnapshot).where(
                BalanceSnapshot.timestamp >= cutoff_date
            ).order_by(BalanceSnapshot.timestamp)
            
            result = await session.execute(stmt)
            snapshots = result.scalars().all()
            
            return [
                {
                    "timestamp": snapshot.timestamp.isoformat(),
                    "value": snapshot.total_balance
                }
                for snapshot in snapshots
            ]
    
    async def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取订单历史"""
        async with get_session_maker()() as session:
            stmt = select(OrderRecord)
            
            if symbol:
                stmt = stmt.where(OrderRecord.symbol == symbol)
            
            stmt = stmt.order_by(desc(OrderRecord.created_time)).limit(limit)
            
            result = await session.execute(stmt)
            orders = result.scalars().all()
            
            return [
                {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "type": order.type,
                    "amount": order.amount,
                    "price": order.price,
                    "filled": order.filled,
                    "status": order.status,
                    "order_type_detail": order.order_type_detail,
                    "created_time": order.created_time.isoformat(),
                    "filled_time": order.filled_time.isoformat() if order.filled_time else None,
                    "cost": order.cost,
                    "fee": order.fee
                }
                for order in orders
            ]
    
    async def get_trade_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取交易统计"""
        async with get_session_maker()() as session:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # 总交易次数
            total_trades_stmt = select(func.count(TradeRecord.id)).where(
                TradeRecord.trade_time >= cutoff_date
            )
            total_trades_result = await session.execute(total_trades_stmt)
            total_trades = total_trades_result.scalar() or 0
            
            # 总交易量
            total_volume_stmt = select(func.sum(TradeRecord.cost)).where(
                TradeRecord.trade_time >= cutoff_date
            )
            total_volume_result = await session.execute(total_volume_stmt)
            total_volume = total_volume_result.scalar() or 0.0
            
            # 获取当前余额
            latest_balance_stmt = select(BalanceSnapshot).order_by(
                desc(BalanceSnapshot.timestamp)
            ).limit(1)
            latest_balance_result = await session.execute(latest_balance_stmt)
            latest_balance = latest_balance_result.scalar_one_or_none()
            
            # 获取初始余额
            init_time = await self.get_init_timestamp()
            if init_time:
                earliest_balance_stmt = select(BalanceSnapshot).where(
                    BalanceSnapshot.timestamp >= init_time
                ).order_by(BalanceSnapshot.timestamp).limit(1)
                earliest_balance_result = await session.execute(earliest_balance_stmt)
                earliest_balance = earliest_balance_result.scalar_one_or_none()
            else:
                earliest_balance = None
            
            # 计算总盈亏
            total_pnl = 0.0
            if latest_balance and earliest_balance:
                total_pnl = latest_balance.total_balance - earliest_balance.total_balance
            
            # 活跃持仓数量
            try:
                positions = await self.trader.get_positions()
                active_positions = len(positions)
            except:
                active_positions = 0
            
            return {
                "totalTrades": total_trades,
                "totalVolume": total_volume,
                "totalPnl": total_pnl,
                "totalPnlPercent": (total_pnl / earliest_balance.total_balance * 100) if earliest_balance and earliest_balance.total_balance > 0 else 0.0,
                "winRate": 65,  # TODO: 计算实际胜率
                "avgTradeSize": total_volume / total_trades if total_trades > 0 else 0.0,
                "maxDrawdown": -5.2,  # TODO: 计算实际最大回撤
                "sharpeRatio": 1.25,  # TODO: 计算实际夏普比率
                "activePositions": active_positions
            }


# 全局服务实例
_history_service_instance: Optional[TradingHistoryService] = None


def get_history_service() -> TradingHistoryService:
    """获取历史服务实例"""
    global _history_service_instance
    if _history_service_instance is None:
        _history_service_instance = TradingHistoryService()
    return _history_service_instance