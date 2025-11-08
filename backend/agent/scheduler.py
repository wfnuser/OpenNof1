"""
Agent Scheduler - Timing and scheduling logic for AI agent decision making
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from agent.workflow import create_trading_workflow
from config.settings import config
from utils.logger import logger

logger = logging.getLogger("AlphaTransformer")


class AgentScheduler:
    """AI Agent 调度器 - 按配置间隔执行分析"""
    
    def __init__(self):
        # 创建工具列表
        from agent.tools import tech_analysis_tool
        tools = [tech_analysis_tool]
        
        self.workflow_chain = create_trading_workflow(tools)
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.stop_event = asyncio.Event()
        
    async def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行")
            return
            
        logger.info(f"启动 AI 调度器，决策间隔: {config.agent.decision_interval} 秒")
        self.is_running = True
        self.stop_event.clear()
        
        # 启动调度任务
        self.task = asyncio.create_task(self._scheduler_loop())
        
    async def stop(self):
        """停止调度器"""
        if not self.is_running:
            logger.warning("调度器未在运行")
            return
            
        logger.info("停止 AI 调度器")
        self.is_running = False
        self.stop_event.set()
        
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
                
    async def _scheduler_loop(self):
        """调度器主循环"""
        logger.info("调度器主循环开始")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                start_time = datetime.now()
                
                # 执行一次完整的分析
                await self._run_single_analysis()
                
                # 计算下次执行时间
                execution_duration = (datetime.now() - start_time).total_seconds()
                wait_time = max(0, config.agent.decision_interval - execution_duration)
                
                logger.info(f"分析完成，耗时 {execution_duration:.2f}s，等待 {wait_time:.2f}s 后下次执行")
                
                # 等待指定时间或停止信号
                try:
                    await asyncio.wait_for(self.stop_event.wait(), timeout=wait_time)
                    # 如果收到停止信号，退出循环
                    break
                except asyncio.TimeoutError:
                    # 超时继续下一轮分析
                    continue
                    
            except asyncio.CancelledError:
                logger.info("调度器任务被取消")
                break
            except Exception as e:
                logger.error(f"调度器执行出错: {e}")
                # 出错后等待一段时间再重试
                try:
                    await asyncio.wait_for(self.stop_event.wait(), timeout=30)
                    break
                except asyncio.TimeoutError:
                    continue
                    
        logger.info("调度器主循环结束")
        
    async def _run_single_analysis(self):
        """执行单次分析"""
        try:
            logger.info("开始执行 AI 交易分析")
            
            # 1. 记录余额快照
            await self._record_balance_snapshot()
            
            # 2. 同步最新的订单和交易数据
            await self._sync_recent_data()
            
            # 3. 准备初始状态
            initial_state = {
                "symbol_decisions": {},
                "overall_summary": None,
                "error": None,
                "analysis_metadata": {
                    "scheduled_run": True,
                    "run_timestamp": datetime.now().isoformat()
                }
            }
            
            # 4. 执行工作流程（包含 save_analysis_node）
            result = await self.workflow_chain.ainvoke(initial_state)
            
            if result.get("error"):
                logger.error(f"分析执行失败: {result['error']}")
            else:
                symbols_count = len(result.get("symbol_decisions", {}))
                logger.info(f"分析执行成功，处理了 {symbols_count} 个标的")
                
        except Exception as e:
            logger.error(f"执行分析时发生错误: {e}")
            # 对于错误情况，工作流程中的 save_analysis_node 会处理保存
            pass
    
    async def _record_balance_snapshot(self):
        """记录余额快照"""
        try:
            from trading.history_service import get_history_service
            history_service = get_history_service()
            await history_service.record_balance_snapshot()
        except Exception as e:
            logger.error(f"记录余额快照失败: {e}")
    
    async def _sync_recent_data(self):
        """同步最新的订单和交易数据"""
        try:
            from trading.history_service import get_history_service
            history_service = get_history_service()
            
            # 只同步最近的数据，避免每次都全量同步
            # 这里可以根据需要调整同步策略
            await history_service.sync_historical_orders()
            await history_service.sync_historical_trades()
            
        except Exception as e:
            logger.error(f"同步最新数据失败: {e}")
            # 这个错误不应该影响AI分析，所以只记录日志
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "decision_interval": config.agent.decision_interval,
            "symbols": config.agent.symbols,
            "timeframes": config.agent.timeframes,
            "model_name": config.agent.model_name,
            "last_run": None,  # TODO: 可以添加最后运行时间记录
            "next_run": None,   # TODO: 可以添加下次运行时间
        }


# 全局调度器实例
_scheduler_instance: Optional[AgentScheduler] = None


def get_scheduler() -> AgentScheduler:
    """获取全局调度器实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AgentScheduler()
    return _scheduler_instance


@asynccontextmanager
async def scheduler_lifespan():
    """调度器生命周期管理（用于 FastAPI 启动/关闭）"""
    scheduler = get_scheduler()
    
    try:
        yield scheduler
    finally:
        if scheduler.is_running:
            await scheduler.stop()