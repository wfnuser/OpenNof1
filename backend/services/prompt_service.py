"""
提示词管理服务 - 三层优先级：数据库 > 配置文件 > 代码默认
"""
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_session_maker
from database.models import SystemConfig
from config.settings import config

logger = logging.getLogger("AlphaTransformer")

# 代码默认的交易策略
DEFAULT_TRADING_STRATEGY = """1. 单一币种仓位上限为可用余额的 20%
2. 止损止盈 - 可以用小时级 NATR 为单位，盈亏比 2:1

原则:
1. 不要随意建仓，除非所有指标都指向一个方向，否则不要轻易下单
2. 不要随意主动平仓，因为已经设置了止盈止损了 - 除非有强烈的信号指示趋势已经反转，才需要平仓"""

# 缓存配置
_strategy_cache: Optional[str] = None
_cache_valid = False


async def get_trading_strategy() -> str:
    """
    获取交易策略配置，按优先级：数据库 > 配置文件 > 代码默认
    """
    global _strategy_cache, _cache_valid

    # 先检查缓存
    if _cache_valid and _strategy_cache is not None:
        return _strategy_cache

    try:
        # 1. 优先级最高：检查数据库
        async with get_session_maker()() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.key == "trading_strategy")
            )
            config_row = result.scalar_one_or_none()

            if config_row and config_row.value.strip():
                logger.info("使用数据库中的交易策略配置")
                _strategy_cache = config_row.value.strip()
                _cache_valid = True
                return _strategy_cache

    except Exception as e:
        logger.warning(f"读取数据库交易策略失败: {e}")

    # 2. 次优先级：检查配置文件
    try:
        config_strategy = getattr(config.agent, 'trading_strategy', None)
        if config_strategy and config_strategy.strip():
            logger.info("使用配置文件中的交易策略配置")
            _strategy_cache = config_strategy.strip()
            _cache_valid = True
            return _strategy_cache
    except Exception as e:
        logger.warning(f"读取配置文件交易策略失败: {e}")

    # 3. 最低优先级：使用代码默认
    logger.info("使用代码默认的交易策略配置")
    _strategy_cache = DEFAULT_TRADING_STRATEGY
    _cache_valid = True
    return _strategy_cache


async def set_trading_strategy(strategy: str) -> bool:
    """
    设置用户自定义的交易策略（存储到数据库）
    """
    global _strategy_cache, _cache_valid

    try:
        if not strategy or not strategy.strip():
            raise ValueError("交易策略内容不能为空")

        strategy = strategy.strip()

        async with get_session_maker()() as session:
            # 查找现有配置
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.key == "trading_strategy")
            )
            config_row = result.scalar_one_or_none()

            if config_row:
                # 更新现有配置
                config_row.value = strategy
                logger.info("更新数据库中的交易策略配置")
            else:
                # 创建新配置
                new_config = SystemConfig(
                    key="trading_strategy",
                    value=strategy,
                    description="用户自定义的交易策略配置"
                )
                session.add(new_config)
                logger.info("创建新的交易策略配置")

            await session.commit()

            # 清除缓存，强制下次重新读取
            _strategy_cache = None
            _cache_valid = False

            return True

    except Exception as e:
        logger.error(f"设置交易策略失败: {e}")
        return False


def clear_strategy_cache():
    """清除策略缓存（用于测试或强制刷新）"""
    global _strategy_cache, _cache_valid
    _strategy_cache = None
    _cache_valid = False
    logger.info("交易策略缓存已清除")