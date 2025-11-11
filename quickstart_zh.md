# 快速开始指南

> 📖 **English**: [Quick Start Guide](./quickstart.md)

## 系统要求

- Python 3.11+
- OpenAI API key (用于 AI 交易决策)
- Binance Futures API 凭证

## 安装步骤

### 1. 克隆代码库
```bash
git clone <repository-url>
cd AlphaTransformer
```

### 2. 安装系统依赖
首先安装 TA-Lib 系统库：

**macOS:**
```bash
brew install ta-lib
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install libta-lib-dev
```

**Windows:**
从此链接下载安装: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

### 3. 安装项目依赖
```bash
# 后端依赖
cd backend
uv sync

# 前端依赖
cd ../frontend
pnpm install
```

### 4. 配置环境变量
```bash
# 创建环境变量文件
cd backend
cp .env.example .env
```

编辑 `.env` 文件，添加你的 API 凭证：

```bash
# AI 提供商 API Key (默认使用 DeepSeek)
OPENAI_API_KEY=your-deepseek-api-key-here

# Binance Futures API (交易必需)
BINANCE_API_KEY=your-binance-api-key-here
BINANCE_API_SECRET=your-binance-api-secret-here

# 数据库配置 (可选 - 默认使用 SQLite)
# DATABASE_URL=sqlite:///./alphatransformer.db
```

**API Key 获取方式:**

1. **AI 提供商 API Key** (统一使用 `OPENAI_API_KEY` 环境变量):
   - **默认配置**: DeepSeek API - 获取地址: https://platform.deepseek.com/api-keys
   - **如需更换其他模型**: 在 `backend/config/agent.yaml` 中修改:
     ```yaml
     agent:
       model_name: "deepseek-chat"  # 改为: gpt-4o, claude-3-5-sonnet, qwen-plus 等
       base_url: "https://api.deepseek.com/v1"  # 对应修改 base_url
       api_key: "${OPENAI_API_KEY}"
     ```

2. **Binance API**: 
   - **注册 Binance**: https://accounts.maxweb.red/register?ref=899414088 (享受返佣优惠)
   - 进入 Binance Futures → API 管理
   - 创建 API key 并启用 "期货交易" 权限
   - ⚠️ **重要**: 如使用实盘交易需启用 "通用转账" 权限
   - 测试环境: 使用 Binance Testnet (testnet.binancefuture.com)
   - ❗ **目前仅支持 Binance Futures**，如需其他交易所请提交 Issue

**注意**: 系统会自动读取.env文件中的环境变量并替换配置文件中的${VAR_NAME}占位符。

### 5. 配置交易代理
编辑 `backend/config/agent.yaml` 来自定义:
- AI 提供商设置 (model_name, base_url, api_key)
- 交易品种
- 风险参数
- 决策间隔

示例配置：
```yaml
agent:
  model_name: "deepseek-chat"  # 或 "gpt-4o", "claude-3-5-sonnet"
  base_url: "https://api.deepseek.com/v1"  # 或 null (OpenAI), 自定义 URL
  api_key: "${OPENAI_API_KEY}"  # 或 "${DEEPSEEK_API_KEY}"
  decision_interval: 180
  symbols:
    - BTCUSDT
    - ETHUSDT

default_risk:
  max_position_size_percent: 0.1
  max_daily_loss_percent: 0.05
```

## 运行系统

### 1. 数据库设置
```bash
# SQLite 数据库会在首次运行时自动创建
# 无需手动设置
```

### 2. 启动交易代理
```bash
cd backend
uv run python main.py
```

代理会：
1. 连接市场数据源
2. 每 60 秒进行一次交易决策
3. 通过 Binance Futures 执行交易
4. 记录所有决策和执行过程

### 3. 启动前端面板
```bash
# 新开一个终端
cd frontend
pnpm run dev
```

## 监控面板

### Web 交易面板
访问地址: `http://localhost:3000`

功能特性：
- 实时持仓监控
- 决策历史和推理过程
- 性能指标统计
- 账户快照记录

### API 接口
```bash
# 获取账户数据
curl http://localhost:8000/api/account

# 获取盈亏历史
curl http://localhost:8000/api/pnl

# 获取持仓数据
curl http://localhost:8000/api/positions

# 获取代理分析
curl http://localhost:8000/api/analysis
```

## 配置选项

### 代理提示词自定义
修改 `config/agent.yaml` 中的 `system_prompt` 来改变代理行为：

```yaml
agent:
  system_prompt: |
    你是一个保守的加密货币交易员，专注于资本保值。
    只进行高概率交易，风险收益比 > 3:1。
    始终遵守仓位大小限制和止损规则。
```

### 风险管理
调整配置中的风险参数：

```yaml
default_risk:
  max_position_size_percent: 0.05  # 每个仓位 5%
  max_daily_loss_percent: 0.03     # 日最大损失 3%
  stop_loss_percent: 0.015         # 止损 1.5%
```

### 交易品种
在交易列表中添加或删除品种：

```yaml
agent:
  symbols:
    - BTCUSDT
    - ETHUSDT
    - SOLUSDT
    - ADAUSDT
```

## 安全功能

### 模拟交易模式
测试时，在配置中启用模拟交易：

```yaml
exchange:
  testnet: true  # 使用 Binance 测试网
```

### 风险控制
系统包含多重安全防护：
- 仓位大小限制
- 日损失限制
- 止损强制执行
- 紧急停止机制

### 监控警报
为重要事件配置警报：

```yaml
logging:
  level: "INFO"
  save_decisions: true
  save_executions: true
```

## 故障排除

### 常见问题

**代理不做决策:**
- 检查 .env 文件中的 API 凭证
- 验证 OpenAI API key 是否有效
- 检查市场数据连接

**订单执行失败:**
- 验证 Binance API 权限
- 检查账户余额
- 审查风险限制设置

**数据库连接错误:**
- 检查 .env 中的 DATABASE_URL
- 确保数据库文件路径可写
- 首次设置时运行数据库初始化

### 调试模式
启用调试日志以详细排除故障：

```yaml
logging:
  level: "DEBUG"
```

## 下一步

1. **模拟交易测试**: 始终先用测试网验证配置
2. **监控性能**: 审查决策质量和执行结果
3. **调整参数**: 根据性能优化风险参数
4. **逐步扩展**: 从小仓位开始

## 支持

- 查看 `logs/` 目录中的日志
- 在 `http://localhost:8000/docs` 检查 API 文档
- 在面板中监控实时数据

## 重要提醒

⚠️ **风险警告**: 这是一个自动交易系统。请从小金额和模拟交易模式开始。

⚠️ **市场风险**: 加密货币市场高度波动。只交易你能承受损失的资金。

⚠️ **API 限制**: 监控你的 API 使用量以避免限速问题。