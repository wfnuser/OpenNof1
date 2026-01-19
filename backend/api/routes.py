"""
API routing module
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from market.data_cache import kline_cache
from market.websocket_client import ws_client
from agent.workflow import create_trading_workflow
from agent.tools.analysis_tools import create_tech_analysis_tool
from agent.models import analysis_service
from agent.scheduler import get_scheduler
from database.database import init_database
from config.settings import config
from utils.logger import logger
from trading.binance_futures import get_trader
from trading.position_service import get_position_service
from services.prompt_service import get_trading_strategy, set_trading_strategy

from functools import wraps
from fastapi import HTTPException, status
router = APIRouter()


# Response models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    uptime_seconds: int
    websocket_connected: bool
    total_symbols: int
    active_timeframes: int


class SymbolsResponse(BaseModel):
    symbols: List[str]
    timeframes: List[str]


class KlineResponse(BaseModel):
    symbol: str
    timeframe: str
    data: List[Dict[str, Any]]


class CacheInfoResponse(BaseModel):
    total_symbols: int
    max_klines_per_timeframe: int
    symbol_details: Dict[str, Dict[str, Any]]


def check_control_permission(func):
    """装饰器：检查控制操作权限"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not config.system.allow_control_operations:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Control operations are disabled for security reasons. Set allow_control_operations=true in agent.yaml to enable."
            )
        return await func(*args, **kwargs)
    return wrapper


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check"""
    status = ws_client.get_status()
    
    return HealthResponse(
        status="healthy" if status.connected else "unhealthy",
        timestamp=datetime.now(),
        uptime_seconds=0,  # TODO: Implement uptime calculation
        websocket_connected=status.connected,
        total_symbols=len(config.agent.symbols),
        active_timeframes=len(config.agent.timeframes)
    )


@router.get("/symbols", response_model=SymbolsResponse)
async def get_symbols():
    """Get configured symbols and timeframes"""
    return SymbolsResponse(
        symbols=config.agent.symbols,
        timeframes=config.agent.timeframes
    )


@router.get("/klines/{symbol}/{timeframe}", response_model=KlineResponse)
async def get_klines(symbol: str, timeframe: str, limit: Optional[int] = None):
    """Get kline data"""
    if symbol not in config.agent.symbols:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not configured")
    
    if timeframe not in config.agent.timeframes:
        raise HTTPException(status_code=404, detail=f"Timeframe {timeframe} not configured")
    
    klines = await kline_cache.get_klines(symbol, timeframe, limit)
    
    if not klines:
        return KlineResponse(
            symbol=symbol,
            timeframe=timeframe,
            data=[]
        )
    
    # Convert to dictionary format
    data = []
    for kline in klines:
        data.append({
            "open_time": kline.open_time,
            "close_time": kline.close_time,
            "open_price": float(kline.open_price),
            "high_price": float(kline.high_price),
            "low_price": float(kline.low_price),
            "close_price": float(kline.close_price),
            "volume": float(kline.volume),
            "quote_volume": float(kline.quote_volume),
            "trades_count": kline.trades_count,
            "is_final": kline.is_final,
            "timestamp": kline.timestamp.isoformat()
        })
    
    return KlineResponse(
        symbol=symbol,
        timeframe=timeframe,
        data=data
    )


@router.get("/snapshot/{symbol}")
async def get_symbol_snapshot(symbol: str):
    """Get symbol snapshot for all timeframes"""
    if symbol not in config.agent.symbols:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not configured")
    
    snapshot = {}
    
    for timeframe in config.agent.timeframes:
        latest = await kline_cache.get_latest_kline(symbol, timeframe)
        if latest:
            snapshot[timeframe] = {
                "open_time": latest.open_time,
                "close_price": float(latest.close_price),
                "volume": float(latest.volume),
                "is_final": latest.is_final,
                "timestamp": latest.timestamp.isoformat()
            }
        else:
            snapshot[timeframe] = None
    
    return {
        "symbol": symbol,
        "snapshot": snapshot,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/cache/info", response_model=CacheInfoResponse)
async def get_cache_info():
    """Get cache information"""
    info = await kline_cache.get_cache_info()
    return CacheInfoResponse(**info)


@router.get("/connection/status")
async def get_connection_status():
    """Get connection status"""
    status = ws_client.get_status()
    return {
        "exchange": status.exchange,
        "connected": status.connected,
        "last_message": status.last_message.isoformat() if status.last_message else None,
        "reconnect_count": status.reconnect_count,
        "error_message": status.error_message
    }


@router.get("/config")
async def get_system_config():
    """Get system configuration"""
    return {
        "agent": {
            "model_name": config.agent.model_name,
            "decision_interval": config.agent.decision_interval,
            "symbols": config.agent.symbols,
            "timeframes": config.agent.timeframes
        },
        "exchange": {
            "name": config.exchange.name,
            "testnet": config.exchange.testnet,
            "websocket_url": config.exchange.get_websocket_url(),
            "rest_api_url": config.exchange.get_rest_api_url()
        },
        "system": {
            "host": config.system.host,
            "port": config.system.port,
            "log_level": config.system.log_level,
            "allow_control_operations": config.system.allow_control_operations
        },
        "risk": {
            "max_position_size_percent": config.default_risk.max_position_size_percent,
            "max_daily_loss_percent": config.default_risk.max_daily_loss_percent,
            "stop_loss_percent": config.default_risk.stop_loss_percent
        }
    }


@router.get("/config/validate")
async def validate_config():
    """Validate system configuration"""
    missing_vars = config.validate_required_env_vars()
    
    return {
        "valid": len(missing_vars) == 0,
        "missing_env_vars": missing_vars,
        "testnet_mode": config.is_testnet_mode(),
        "agent_configured": bool(config.agent.api_key and not config.agent.api_key.startswith('${')),
        "exchange_configured": bool(
            config.exchange.api_key and 
            config.exchange.api_secret and 
            not config.exchange.api_key.startswith('${') and
            not config.exchange.api_secret.startswith('${')
        )
    }


# Agent analysis response models
class SymbolDecisionResponse(BaseModel):
    symbol: str
    action: str
    reasoning: str
    execution_status: str
    execution_result: Optional[Dict[str, Any]] = None


class AgentAnalysisResponse(BaseModel):
    symbol_decisions: Dict[str, SymbolDecisionResponse]
    overall_summary: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float


# Agent endpoints
@router.post("/agent/analyze", response_model=AgentAnalysisResponse)
async def run_agent_analysis():
    """Run AI agent analysis and trading workflow"""
    try:
        logger.info("开始运行 Agent 分析...")
        
        # 确保数据库已初始化
        await init_database()
        
        # 创建技术分析工具
        tech_tool = create_tech_analysis_tool()
        tools = [tech_tool]
        
        # 创建工作流程
        workflow = create_trading_workflow(tools)
        
        # 初始状态
        from agent.state import AgentState
        initial_state: AgentState = {
            "symbol_decisions": {},
            "overall_summary": None,
            "error": None
        }
        
        # 运行工作流程
        start_time = datetime.now()
        result = await workflow.ainvoke(initial_state)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # 构建响应
        symbol_decisions_response = {}
        for symbol, decision in result["symbol_decisions"].items():
            symbol_decisions_response[symbol] = SymbolDecisionResponse(
                symbol=symbol,
                action=decision["action"],
                reasoning=decision["reasoning"],
                execution_status=decision["execution_status"],
                execution_result=decision["execution_result"]
            )
        
        response = AgentAnalysisResponse(
            symbol_decisions=symbol_decisions_response,
            overall_summary=result.get("overall_summary"),
            error=result.get("error"),
            duration_ms=duration_ms
        )
        
        logger.info(f"Agent 分析完成: {len(result['symbol_decisions'])} 个标的决策 (耗时: {duration_ms:.2f}ms)")
        return response
        
    except Exception as e:
        logger.error(f"Agent 分析失败: {e}")
        return AgentAnalysisResponse(
            symbol_decisions={},
            overall_summary=f"Agent 分析失败: {str(e)}",
            error=str(e),
            duration_ms=0.0
        )


class DecisionResponse(BaseModel):
    id: int
    timestamp: datetime
    analysis_id: str
    overall_summary: Optional[str] = None
    symbol_decisions: Dict[str, Any]
    model_name: str
    duration_ms: Optional[float] = None


@router.get("/decisions", response_model=List[DecisionResponse])
async def get_decisions(limit: int = 100, offset: int = 0, order: str = "desc"):
    """Get recent trading analyses"""
    try:
        order_normalized = (order or "desc").lower()
        if order_normalized not in {"asc", "desc"}:
            raise HTTPException(status_code=400, detail="Invalid order parameter")

        analyses = await analysis_service.get_recent_analyses(
            limit=limit,
            offset=offset,
            order=order_normalized
        )
        
        response = []
        for analysis in analyses:
            response.append(DecisionResponse(
                id=analysis.id,
                timestamp=analysis.timestamp,
                analysis_id=analysis.analysis_id,
                overall_summary=analysis.overall_summary,
                symbol_decisions=analysis.symbol_decisions,
                model_name=analysis.model_name,
                duration_ms=analysis.duration_ms
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"获取分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析失败: {str(e)}")


class DecisionStatsResponse(BaseModel):
    period_days: int
    total_analyses: int
    avg_duration_ms: float


@router.get("/decisions/stats", response_model=DecisionStatsResponse)
async def get_decision_stats(days: int = 7):
    """Get analysis statistics"""
    try:
        stats = await analysis_service.get_analysis_stats(days=days)
        
        return DecisionStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"获取分析统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析统计失败: {str(e)}")


# Agent control response models
class AgentControlResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime


class AgentStatusResponse(BaseModel):
    is_running: bool
    decision_interval: int
    symbols: List[str]
    timeframes: List[str]
    model_name: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    uptime_seconds: Optional[int] = None


# Agent control endpoints
@router.post("/agent/start", response_model=AgentControlResponse)
@check_control_permission
async def start_agent():
    """启动 AI Agent 调度器"""
    try:
        scheduler = get_scheduler()
        
        if scheduler.is_running:
            return AgentControlResponse(
                success=False,
                message="Agent 已在运行中",
                timestamp=datetime.now()
            )
        
        # 确保数据库已初始化
        await init_database()
        
        # 启动调度器
        await scheduler.start()
        
        logger.info("AI Agent 调度器启动成功")
        return AgentControlResponse(
            success=True,
            message="Agent 启动成功",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"启动 Agent 失败: {e}")
        return AgentControlResponse(
            success=False,
            message=f"启动 Agent 失败: {str(e)}",
            timestamp=datetime.now()
        )


@router.post("/agent/stop", response_model=AgentControlResponse)
@check_control_permission
async def stop_agent():
    """停止 AI Agent 调度器"""
    try:
        scheduler = get_scheduler()
        
        if not scheduler.is_running:
            return AgentControlResponse(
                success=False,
                message="Agent 未在运行",
                timestamp=datetime.now()
            )
        
        # 停止调度器
        await scheduler.stop()
        
        logger.info("AI Agent 调度器停止成功")
        return AgentControlResponse(
            success=True,
            message="Agent 停止成功",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"停止 Agent 失败: {e}")
        return AgentControlResponse(
            success=False,
            message=f"停止 Agent 失败: {str(e)}",
            timestamp=datetime.now()
        )


@router.get("/agent/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """获取 AI Agent 状态"""
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()
        
        return AgentStatusResponse(
            is_running=status["is_running"],
            decision_interval=status["decision_interval"],
            symbols=status["symbols"],
            timeframes=status["timeframes"],
            model_name=status["model_name"],
            last_run=status.get("last_run"),
            next_run=status.get("next_run"),
            uptime_seconds=status.get("uptime_seconds")
        )
        
    except Exception as e:
        logger.error(f"获取 Agent 状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取 Agent 状态失败: {str(e)}")


# Trading API Models


class PositionResponse(BaseModel):
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    percentage_pnl: float
    leverage: float
    margin: float
    timestamp: datetime


class BalanceResponse(BaseModel):
    total_balance: float
    available_balance: float
    margin_balance: float
    unrealized_pnl: float
    currency: str
    timestamp: datetime


class AccountSummaryResponse(BaseModel):
    balance: Dict[str, Any]
    positions: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    timestamp: str


# Trading Endpoints
@router.get("/trading/balance", response_model=BalanceResponse)
async def get_trading_balance():
    """获取交易账户余额"""
    try:
        trader = get_trader()
        balance = await trader.get_balance()
        
        return BalanceResponse(
            total_balance=balance.total_balance,
            available_balance=balance.available_balance,
            margin_balance=balance.margin_balance,
            unrealized_pnl=balance.unrealized_pnl,
            currency=balance.currency,
            timestamp=balance.timestamp
        )
        
    except Exception as e:
        logger.error(f"获取交易余额失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易余额失败: {str(e)}")


@router.get("/trading/positions", response_model=List[PositionResponse])
async def get_trading_positions():
    """获取当前持仓"""
    try:
        trader = get_trader()
        positions = await trader.get_positions()
        
        return [
            PositionResponse(
                symbol=pos.symbol,
                side=pos.side,
                size=pos.size,
                entry_price=pos.entry_price,
                mark_price=pos.mark_price,
                unrealized_pnl=pos.unrealized_pnl,
                percentage_pnl=pos.percentage_pnl,
                leverage=pos.leverage,
                margin=pos.margin,
                timestamp=pos.timestamp
            )
            for pos in positions
        ]
        
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")


@router.get("/trading/account/summary", response_model=AccountSummaryResponse)
async def get_account_summary():
    """获取账户概览"""
    try:
        position_service = get_position_service()
        summary = await position_service.get_account_summary()
        
        return AccountSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"获取账户概览失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取账户概览失败: {str(e)}")





@router.get("/trading/market/{symbol}/price")
async def get_market_price(symbol: str):
    """获取市场价格"""
    try:
        trader = get_trader()
        price = await trader.get_market_price(symbol)
        
        return {
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取 {symbol} 价格失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取价格失败: {str(e)}")


# 历史数据相关API
class BalanceHistoryResponse(BaseModel):
    timestamp: str
    value: float


class OrderHistoryResponse(BaseModel):
    order_id: str
    symbol: str
    side: str
    type: str
    amount: float
    price: Optional[float] = None
    filled: float
    status: str
    order_type_detail: Optional[str] = None
    created_time: str
    filled_time: Optional[str] = None
    cost: float
    fee: float


class TradeStatsResponse(BaseModel):
    totalTrades: int
    totalVolume: float
    totalPnl: float
    totalPnlPercent: float
    winRate: float
    avgTradeSize: float
    maxDrawdown: float
    sharpeRatio: float
    activePositions: int


@router.get("/trading/balance/history", response_model=List[BalanceHistoryResponse])
async def get_balance_history(days: int = 30, include_all: bool = False):
    """获取余额历史"""
    try:
        from trading.history_service import get_history_service
        history_service = get_history_service()
        
        balance_history = await history_service.get_balance_history(
            days=None if include_all else days
        )
        
        return [
            BalanceHistoryResponse(
                timestamp=record["timestamp"],
                value=record["value"]
            )
            for record in balance_history
        ]
        
    except Exception as e:
        logger.error(f"获取余额历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取余额历史失败: {str(e)}")


@router.get("/trading/orders/history", response_model=List[OrderHistoryResponse])
async def get_order_history(symbol: Optional[str] = None, limit: int = 100):
    """获取订单历史"""
    try:
        from trading.history_service import get_history_service
        history_service = get_history_service()
        
        order_history = await history_service.get_order_history(symbol=symbol, limit=limit)
        
        return [
            OrderHistoryResponse(**order)
            for order in order_history
        ]
        
    except Exception as e:
        logger.error(f"获取订单历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单历史失败: {str(e)}")


@router.get("/trading/stats", response_model=TradeStatsResponse)
async def get_trade_stats(days: int = 30):
    """获取交易统计"""
    try:
        from trading.history_service import get_history_service
        history_service = get_history_service()
        
        stats = await history_service.get_trade_statistics(days=days)
        
        return TradeStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"获取交易统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易统计失败: {str(e)}")


@router.post("/trading/history/reset")
@check_control_permission
async def reset_trading_history(init_time: Optional[str] = None):
    """重置交易历史系统（清空所有数据并重新初始化）"""
    try:
        from trading.history_service import get_history_service
        history_service = get_history_service()
        
        # 解析初始化时间
        parsed_init_time = None
        if init_time:
            try:
                parsed_init_time = datetime.fromisoformat(init_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的时间格式，请使用ISO格式")
        
        # 重置系统
        result = await history_service.reset_system(parsed_init_time)
        
        return result
        
    except Exception as e:
        logger.error(f"重置交易历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")


@router.post("/trading/history/sync")
@check_control_permission
async def sync_trading_history(full_sync: bool = False):
    """手动同步交易历史"""
    try:
        from trading.history_service import get_history_service
        history_service = get_history_service()
        
        if full_sync:
            order_count = await history_service.sync_historical_orders(full_sync=True)
            trade_count = await history_service.sync_historical_trades(full_sync=True)
        else:
            order_count = await history_service.sync_recent_orders(24)
            trade_count = await history_service.sync_recent_trades(24)
        
        # 记录当前余额快照
        await history_service.record_balance_snapshot()
        
        return {
            "success": True,
            "message": f"{'全量' if full_sync else '增量'}同步完成",
            "synced_orders": order_count,
            "synced_trades": trade_count
        }
        
    except Exception as e:
        logger.error(f"同步交易历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


# Trading Strategy API Models
class TradingStrategyResponse(BaseModel):
    strategy: str
    source: str  # "database", "config", or "default"

class TradingStrategyRequest(BaseModel):
    strategy: str

class TradingStrategyUpdateResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime


# Trading Strategy Endpoints
@router.get("/trading/strategy", response_model=TradingStrategyResponse)
async def get_current_trading_strategy():
    """获取当前交易策略配置"""
    try:
        strategy = await get_trading_strategy()
        
        # 检查来源
        from database.database import get_session_maker
        from database.models import SystemConfig
        from sqlalchemy import select
        
        source = "default"
        try:
            async with get_session_maker()() as session:
                result = await session.execute(
                    select(SystemConfig).where(SystemConfig.key == "trading_strategy")
                )
                config_row = result.scalar_one_or_none()
                
                if config_row and config_row.value.strip():
                    source = "database"
                elif hasattr(config.agent, 'trading_strategy') and config.agent.trading_strategy:
                    source = "config"
        except Exception:
            pass
        
        return TradingStrategyResponse(
            strategy=strategy,
            source=source
        )
        
    except Exception as e:
        logger.error(f"获取交易策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易策略失败: {str(e)}")


@router.post("/trading/strategy", response_model=TradingStrategyUpdateResponse)
@check_control_permission
async def update_trading_strategy(request: TradingStrategyRequest):
    """更新用户自定义交易策略"""
    try:
        if not request.strategy or not request.strategy.strip():
            raise HTTPException(status_code=400, detail="交易策略内容不能为空")
        
        success = await set_trading_strategy(request.strategy.strip())
        
        if success:
            logger.info("用户交易策略更新成功")
            return TradingStrategyUpdateResponse(
                success=True,
                message="交易策略更新成功",
                timestamp=datetime.now()
            )
        else:
            raise HTTPException(status_code=500, detail="更新交易策略失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新交易策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新交易策略失败: {str(e)}")


@router.delete("/trading/strategy", response_model=TradingStrategyUpdateResponse)
@check_control_permission
async def reset_trading_strategy():
    """重置交易策略为默认值（删除数据库中的自定义配置）"""
    try:
        from database.database import get_session_maker
        from database.models import SystemConfig
        from sqlalchemy import select, delete
        
        async with get_session_maker()() as session:
            # 删除数据库中的自定义配置
            await session.execute(
                delete(SystemConfig).where(SystemConfig.key == "trading_strategy")
            )
            await session.commit()
        
        # 清除缓存
        from services.prompt_service import clear_strategy_cache
        clear_strategy_cache()
        
        logger.info("交易策略已重置为默认值")
        return TradingStrategyUpdateResponse(
            success=True,
            message="交易策略已重置为默认值",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"重置交易策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置交易策略失败: {str(e)}")
