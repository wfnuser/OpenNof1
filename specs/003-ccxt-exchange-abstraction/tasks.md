# 任务: CCXT 交易所抽象与 Hyperliquid 支持

**原则**: 简单、渐进、保持现有代码工作

## Phase 1: 接口抽象（保持现有代码工作）

**目标**: 在不破坏现有功能的前提下，抽象出通用交易所接口

- [ ] T001 完善 ExchangeTrader 接口 - `backend/trading/interface.py`
  - 检查现有接口方法是否完整覆盖 BinanceFuturesTrader 的功能
  - 添加缺失的方法签名（如果有）
  - 确保返回类型标准化

- [ ] T002 确保 BinanceFuturesTrader 完整实现接口 - `backend/trading/binance_futures.py`
  - 验证所有接口方法都有实现
  - 标准化返回格式（保持功能不变）
  - 确保现有 agent 代码继续工作

- [ ] T003 创建交易所工厂函数 - `backend/trading/factory.py`
  - 实现简单的 `get_exchange_trader(name=None)` 函数
  - 默认返回现有的币安交易器（向后兼容）
  - 支持通过参数选择交易所

**检查点**: 现有代码完全不变，但现在通过统一接口访问

---

## Phase 2: 添加 Hyperliquid 支持

**目标**: 添加 Hyperliquid 作为第二个交易所选择

- [ ] T004 创建 HyperliquidTrader - `backend/trading/hyperliquid_trader.py`
  - 使用 `ccxt.hyperliquid()` 实现相同的 ExchangeTrader 接口
  - 处理认证（钱包地址 + 私钥）
  - 处理符号映射（"BTC/USDT" -> "BTC"）
  - 实现所有交易方法（open_long, close_long 等）

- [ ] T005 扩展配置支持多交易所 - `backend/config/settings.py`
  - 在现有配置基础上添加交易所选择选项
  - 支持 Hyperliquid 凭据配置
  - 保持向后兼容（默认仍然是币安）

**检查点**: 可以通过配置选择使用币安或 Hyperliquid

---

## 测试验证

```python
# 测试 1: 现有代码仍然工作
from trading.binance_futures import get_trader
trader = get_trader()  # 应该继续工作

# 测试 2: 新的工厂模式
from trading.factory import get_exchange_trader
binance_trader = get_exchange_trader("binance")  # 币安
hyperliquid_trader = get_exchange_trader("hyperliquid")  # Hyperliquid

# 测试 3: 相同的接口
balance1 = await binance_trader.get_balance()
balance2 = await hyperliquid_trader.get_balance()
# 两者返回相同格式的 Balance 对象
```

---

## 总结

- **总任务数**: 5 个核心任务
- **Phase 1**: 3 个任务（接口抽象）
- **Phase 2**: 2 个任务（添加 Hyperliquid）
- **向后兼容**: 100% 保证现有代码继续工作
- **MVP**: 完成 Phase 1 就有了统一接口，完成 Phase 2 就支持双交易所

这样简单多了！