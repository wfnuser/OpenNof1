"""
Analysis Node - ReAct Agent for technical analysis and decision making
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agent.state import AgentState, SymbolDecision
from config.settings import config
from services.prompt_service import get_trading_strategy


class SymbolDecision(BaseModel):
    """单个交易标的的决策"""

    symbol: str = Field(description="交易标的符号，例如 'BTCUSDT'")
    action: str = Field(
        description="期货交易决策，只能是 'OPEN_LONG'(开多仓), 'OPEN_SHORT'(开空仓), 'CLOSE_LONG'(平多仓), 'CLOSE_SHORT'(平空仓) 或 'HOLD'(持仓观望)"
    )
    reasoning: str = Field(description="详细的推理过程，说明为什么做出这个决策")
    position_size_usd: float = Field(
        description="期望的仓位价值(美元)，仅对开仓操作有效，平仓操作会自动全部平仓",
        default=0.0,
    )
    stop_loss_price: Optional[float] = Field(
        description="止损价格，仅对开仓操作有效", default=None
    )
    take_profit_price: Optional[float] = Field(
        description="止盈价格，仅对开仓操作有效", default=None
    )


class TradingDecision(BaseModel):
    """完整的交易决策结构"""

    symbol_decisions: List[SymbolDecision] = Field(description="所有交易标的的决策列表")
    overall_summary: str = Field(description="整体市场状况分析和总结")


logger = logging.getLogger("AlphaTransformer")


# 基础 ReAct agent LLM - 支持自定义服务商
def create_llm():
    """创建LLM实例，支持不同的AI服务商"""
    llm_config = {
        "model": config.agent.model_name,
        "api_key": config.agent.api_key,
        "temperature": 0.1
    }
    
    # 如果配置了自定义base_url，则使用
    if config.agent.base_url:
        llm_config["base_url"] = config.agent.base_url
    
    return ChatOpenAI(**llm_config)

llm = create_llm()

# 结构化输出 LLM - 用于最终决策
def create_structured_llm():
    """创建结构化输出LLM实例，兼容不同AI服务商"""
    llm_config = {
        "model": config.agent.model_name,
        "api_key": config.agent.api_key,
        "temperature": 0.0
    }
    
    if config.agent.base_url:
        llm_config["base_url"] = config.agent.base_url
    
    llm = ChatOpenAI(**llm_config)
    
    # 检查是否支持原生结构化输出 (仅OpenAI gpt-4o系列)
    if config.agent.model_name.startswith("gpt-4o") and config.agent.base_url is None:
        return llm.with_structured_output(TradingDecision)
    else:
        # 其他模型使用JSON mode或普通文本模式
        return llm

def supports_native_structured_output():
    """检查是否支持原生结构化输出"""
    return config.agent.model_name.startswith("gpt-4o") and config.agent.base_url is None

def parse_json_response(response_text: str) -> TradingDecision:
    """解析JSON格式的响应为TradingDecision对象"""
    import json
    import re
    
    # 提取JSON部分（去除markdown代码块标记等）
    json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # 尝试直接解析整个响应
        json_str = response_text.strip()
    
    try:
        json_data = json.loads(json_str)
        return TradingDecision(**json_data)
    except Exception as e:
        logger.error(f"解析JSON响应失败: {e}, 原始响应: {response_text}")
        # 返回默认的HOLD决策
        return TradingDecision(
            symbol_decisions=[
                SymbolDecision(
                    symbol=symbol,
                    action="HOLD",
                    reasoning="JSON解析失败，采用保守策略",
                    position_size_usd=0.0
                ) for symbol in config.agent.symbols
            ],
            overall_summary="由于响应解析错误，所有标的采用观望策略"
        )

structured_llm = create_structured_llm()


def analysis_node(tools: List):
    """Create analysis node function with structured output"""
    react_agent = create_react_agent(llm, tools)

    async def node(state: AgentState) -> AgentState:
        """ReAct 分析节点 - AI 主动调用工具获取技术数据并做出决策"""
        try:
            logger.info("开始 ReAct 分析...")

            # 获取配置中的交易标的
            symbols = config.agent.symbols
            symbols_list = ", ".join(symbols)

            # 获取当前账户状态
            from trading.binance_futures import get_trader

            trader = get_trader()
            balance = await trader.get_balance()
            positions = await trader.get_positions()

            # 格式化账户信息
            balance_info = f"总余额: ${balance.total_balance:.2f}, 可用余额: ${balance.available_balance:.2f}, 未实现盈亏: ${balance.unrealized_pnl:.2f}"

            positions_info = ""
            if positions:
                position_details = []
                for pos in positions:
                    position_details.append(
                        f"{pos.symbol}: {pos.side} {pos.size} (盈亏: ${pos.unrealized_pnl:.2f})"
                    )
                positions_info = f"当前持仓: {', '.join(position_details)}"
            else:
                positions_info = "当前持仓: 无"

            # 第一步：ReAct agent 分析市场数据
            analysis_prompt = f"""
            请分析以下交易标的的当前市场状况：
            
            标的: {symbols_list}
            
            请使用可用的技术分析工具来获取 K 线数据和技术指标。
            分析完成后，为每个标的提供详细的市场分析结果。
            指标包括：RSI、MACD、EMA、NATR（波动率指标）。
            也需要对各个 timeframe 的指标进行细化分析和汇总。
            
            时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """

            # 运行 ReAct agent 进行技术分析
            analysis_result = await react_agent.ainvoke(
                {"messages": [HumanMessage(content=analysis_prompt)]}
            )

            analysis_content = (
                analysis_result["messages"][-1].content
                if analysis_result["messages"]
                else ""
            )
            logger.info(f"{analysis_content}")

            # 第二步：使用新的分层提示词系统生成结构化决策
            
            # 系统提示词（固定结构）
            system_prompt = f"""基于以下信息为每个标的做出交易决策：

标的: {symbols_list}

当前账户状态:
{balance_info}
{positions_info}

技术分析结果:
{analysis_content}

请为每个标的做出期货交易决策：
- OPEN_LONG: 开多仓 (看涨时选择)
- OPEN_SHORT: 开空仓 (看跌时选择) 
- CLOSE_LONG: 平多仓 (将全部平掉多头持仓)
- CLOSE_SHORT: 平空仓 (将全部平掉空头持仓)
- HOLD: 持仓观望 (无明确信号或当前持仓合适)

对于开仓操作(OPEN_LONG/OPEN_SHORT)，请指定：
1. 期望的仓位价值(美元金额)
2. 止损价格
3. 止盈价格

注意：杠杆已配置为{config.get_default_leverage()}x，无需指定。"""

            # 获取用户交易策略（三层优先级）
            user_trading_strategy = await get_trading_strategy()
            
            # 根据是否支持原生结构化输出来调整处理
            if supports_native_structured_output():
                # OpenAI gpt-4o 使用原生结构化输出
                trading_decision = await structured_llm.ainvoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_trading_strategy)
                ])
            else:
                # 其他模型使用JSON格式
                json_schema = {
                    "symbol_decisions": [
                        {
                            "symbol": "string",
                            "action": "OPEN_LONG|OPEN_SHORT|CLOSE_LONG|CLOSE_SHORT|HOLD",
                            "reasoning": "string",
                            "position_size_usd": "number (仅开仓时需要)",
                            "stop_loss_price": "number (仅开仓时，可选)",
                            "take_profit_price": "number (仅开仓时，可选)"
                        }
                    ],
                    "overall_summary": "string"
                }
                
                json_instruction = f"""
请以JSON格式返回决策，严格按照以下格式：

```json
{json.dumps(json_schema, indent=2, ensure_ascii=False)}
```

确保JSON格式正确，所有字符串用双引号包围。"""
                
                response = await structured_llm.ainvoke([
                    SystemMessage(content=system_prompt + json_instruction),
                    HumanMessage(content=user_trading_strategy)
                ])
                
                # 解析JSON响应
                trading_decision = parse_json_response(response.content)

            logger.info(f"trading decision: {trading_decision}")

            # 直接使用 TradingDecision 构建状态
            symbol_decisions = {}
            for decision in trading_decision.symbol_decisions:
                symbol_decisions[decision.symbol] = {
                    "action": decision.action,
                    "reasoning": decision.reasoning,
                    "position_size_usd": decision.position_size_usd,
                    "stop_loss_price": decision.stop_loss_price,
                    "take_profit_price": decision.take_profit_price,
                    "execution_result": None,
                    "execution_status": "pending",
                }

            # 更新状态
            state["symbol_decisions"] = symbol_decisions
            state["overall_summary"] = trading_decision.overall_summary

            logger.info(
                f"ReAct 分析完成: {len(trading_decision.symbol_decisions)} 个标的决策"
            )
            return state

        except Exception as e:
            logger.error(f"ReAct 分析失败: {e}")
            state["symbol_decisions"] = {}
            state["overall_summary"] = f"分析失败: {str(e)}"
            state["error"] = str(e)
            return state

    return node
