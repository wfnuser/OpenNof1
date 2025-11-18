"""
Trading Execution Node - Execute real futures trading decisions
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from agent.state import AgentState
from trading.binance_futures import get_trader
from trading.position_service import get_position_service
from config.settings import config

logger = logging.getLogger("AlphaTransformer")


def _resolve_default_leverage(exchange_name: Optional[str]) -> int:
    return config.get_default_leverage(exchange_name)


async def trading_execution_node(state: AgentState) -> AgentState:
    """真实期货交易执行节点"""
    try:
        symbol_decisions = state["symbol_decisions"]
        trader = get_trader()
        position_service = get_position_service()
        
        logger.info(f"开始执行真实期货交易: {len(symbol_decisions)} 个标的")
        
        # 获取当前账户状态
        try:
            balance = await trader.get_balance()
            positions = await trader.get_positions()
            logger.info(f"账户余额: ${balance.total_balance}, 持仓数量: {len(positions)}")
        except Exception as e:
            logger.error(f"获取账户状态失败: {e}")
            state["error"] = f"获取账户状态失败: {str(e)}"
            return state
        
        # 先执行所有平仓操作，再执行所有开仓操作
        close_decisions = {}
        open_decisions = {}
        
        # 分离平仓和开仓决策
        for symbol, decision in symbol_decisions.items():
            action = decision["action"]
            if action in ["CLOSE_LONG", "CLOSE_SHORT"]:
                close_decisions[symbol] = decision
            elif action in ["OPEN_LONG", "OPEN_SHORT"]:
                open_decisions[symbol] = decision
            elif action == "HOLD":
                # HOLD 操作直接标记为完成
                logger.info(f"{symbol}: HOLD - AI决策持仓观望，无需执行交易操作")
                decision["execution_result"] = {
                    "status": "success",
                    "action": action,
                    "symbol": symbol,
                    "message": "持仓观望，无需执行交易",
                    "timestamp": datetime.now().isoformat()
                }
                decision["execution_status"] = "completed"
        
        # 第一步：执行所有平仓操作
        for symbol, decision in close_decisions.items():
            try:
                execution_result = await _execute_futures_trading(
                    symbol, decision, trader, balance, positions
                )
                decision["execution_result"] = execution_result
                decision["execution_status"] = "completed" if execution_result["status"] == "success" else "failed"
                
            except Exception as e:
                logger.error(f"执行 {symbol} 平仓失败: {e}")
                decision["execution_status"] = "failed"
                decision["execution_result"] = {
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # 第二步：重新获取余额和持仓信息（平仓后可能有变化）
        if close_decisions:
            try:
                balance = await trader.get_balance()
                positions = await trader.get_positions()
                logger.info(f"平仓后账户余额: ${balance.total_balance}, 持仓数量: {len(positions)}")
            except Exception as e:
                logger.error(f"重新获取账户状态失败: {e}")
        
        # 第三步：执行所有开仓操作
        for symbol, decision in open_decisions.items():
            try:
                execution_result = await _execute_futures_trading(
                    symbol, decision, trader, balance, positions
                )
                decision["execution_result"] = execution_result
                decision["execution_status"] = "completed" if execution_result["status"] == "success" else "failed"
                
            except Exception as e:
                logger.error(f"执行 {symbol} 开仓失败: {e}")
                decision["execution_status"] = "failed"
                decision["execution_result"] = {
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        logger.info(f"期货交易执行完成: {len(symbol_decisions)} 个标的")
        return state
        
    except Exception as e:
        logger.error(f"期货交易执行节点失败: {e}")
        state["error"] = str(e)
        return state


async def _execute_futures_trading(symbol: str, decision: Dict[str, Any], trader, balance, positions) -> Dict[str, Any]:
    """执行单个标的的真实期货交易"""
    action = decision["action"]
    timestamp = datetime.now().isoformat()
    
    try:
        # 处理 HOLD 操作
        if action == "HOLD":
            logger.info(f"{symbol}: HOLD - AI决策持仓观望，无需执行交易操作")
            return {
                "status": "success",
                "action": action,
                "symbol": symbol,
                "message": "HOLD操作，无需执行交易",
                "timestamp": timestamp
            }
        
        # 获取当前市场价格
        current_price = await trader.get_market_price(symbol)
        if current_price <= 0:
            raise ValueError(f"无法获取 {symbol} 的有效价格")
        
        # 获取当前持仓 (处理符号格式差异)
        current_position = None
        for pos in positions:
            # 标准化符号比较：SOLUSDT vs SOL/USDT:USDT
            pos_symbol_normalized = pos.symbol.replace('/', '').replace(':USDT', '').replace(':USDC', '')
            symbol_normalized = symbol.replace('/', '').replace(':USDT', '').replace(':USDC', '')
            
            if pos_symbol_normalized == symbol_normalized:
                current_position = pos
                break
        
        # 执行具体的交易操作
        if action == "OPEN_LONG":
            result = await _execute_open_long(symbol, decision, trader, current_price, balance)
        elif action == "OPEN_SHORT":
            result = await _execute_open_short(symbol, decision, trader, current_price, balance)
        elif action == "CLOSE_LONG":
            result = await _execute_close_long(symbol, decision, trader, current_position)
        elif action == "CLOSE_SHORT":
            result = await _execute_close_short(symbol, decision, trader, current_position)
        else:
            raise ValueError(f"不支持的交易操作: {action}")
        
        result["timestamp"] = timestamp
        return result
        
    except Exception as e:
        logger.error(f"执行 {symbol} {action} 失败: {e}")
        return {
            "status": "failed",
            "action": action,
            "symbol": symbol,
            "error": str(e),
            "timestamp": timestamp
        }


async def _execute_open_long(symbol: str, decision: Dict, trader, current_price: float, balance) -> Dict[str, Any]:
    """执行开多仓"""
    position_size_usd = decision.get("position_size_usd", 0)
    leverage = _resolve_default_leverage(trader.get_exchange_name())
    
    # 根据 AI 决策的仓位价值计算交易数量
    quantity = position_size_usd / current_price
    
    # 获取止损止盈价格
    stop_loss_price = decision.get("stop_loss_price")
    take_profit_price = decision.get("take_profit_price")
    
    # 执行开多仓（含止损止盈）
    await trader.open_long(symbol, quantity, leverage, stop_loss_price, take_profit_price)
    
    logger.info(f"开多仓成功: {symbol} 数量:{quantity} 杠杆:{leverage}x 价格:${current_price}")
    
    return {
        "status": "success",
        "action": "OPEN_LONG",
        "symbol": symbol,
        "quantity": quantity,
        "leverage": leverage,
        "price": current_price,
        "message": f"开多仓成功: {quantity} @ ${current_price}"
    }


async def _execute_open_short(symbol: str, decision: Dict, trader, current_price: float, balance) -> Dict[str, Any]:
    """执行开空仓"""
    position_size_usd = decision.get("position_size_usd", 0)
    leverage = _resolve_default_leverage(trader.get_exchange_name())
    
    # 根据 AI 决策的仓位价值计算交易数量
    quantity = position_size_usd / current_price
    
    # 获取止损止盈价格
    stop_loss_price = decision.get("stop_loss_price")
    take_profit_price = decision.get("take_profit_price")
    
    # 执行开空仓（含止损止盈）
    await trader.open_short(symbol, quantity, leverage, stop_loss_price, take_profit_price)
    
    logger.info(f"开空仓成功: {symbol} 数量:{quantity} 杠杆:{leverage}x 价格:${current_price}")
    
    return {
        "status": "success",
        "action": "OPEN_SHORT",
        "symbol": symbol,
        "quantity": quantity,
        "leverage": leverage,
        "price": current_price,
        "message": f"开空仓成功: {quantity} @ ${current_price}"
    }


async def _execute_close_long(symbol: str, decision: Dict, trader, current_position) -> Dict[str, Any]:
    """执行平多仓 - 直接全部平仓"""
    if not current_position or current_position.side != "LONG":
        raise ValueError(f"{symbol} 没有多头持仓可平")
    
    # 执行全部平仓
    await trader.close_long(symbol, 0)  # 0 表示全部平仓
    
    logger.info(f"平多仓成功: {symbol} 数量:{current_position.size}")
    
    return {
        "status": "success",
        "action": "CLOSE_LONG",
        "symbol": symbol,
        "quantity": current_position.size,
        "message": f"平多仓成功: {current_position.size}"
    }


async def _execute_close_short(symbol: str, decision: Dict, trader, current_position) -> Dict[str, Any]:
    """执行平空仓 - 直接全部平仓"""
    if not current_position or current_position.side != "SHORT":
        raise ValueError(f"{symbol} 没有空头持仓可平")
    
    # 执行全部平仓
    await trader.close_short(symbol, 0)  # 0 表示全部平仓
    
    logger.info(f"平空仓成功: {symbol} 数量:{current_position.size}")
    
    return {
        "status": "success",
        "action": "CLOSE_SHORT",
        "symbol": symbol,
        "quantity": current_position.size,
        "message": f"平空仓成功: {current_position.size}"
    }
