# Quick Start Guide

> 📖 **中文文档**: [快速开始指南](./quickstart_zh.md)

## Prerequisites

- Python 3.11+
- OpenAI API key (for agent decisions)
- Binance Futures API credentials

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd AlphaTransformer
```

### 2. Install System Dependencies
First, install TA-Lib system library:

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
Download and install from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

### 3. Install Project Dependencies
```bash
# Backend dependencies
cd backend
uv sync

# Frontend dependencies
cd ../frontend
pnpm install
```

### 4. Setup Environment Variables
```bash
# Create .env file from template
cd backend
cp .env.example .env
```

Edit the `.env` file with your API credentials:

```bash
# AI Provider API Key (defaults to DeepSeek)
OPENAI_API_KEY=your-api-key-here

# Binance Futures API (required for trading)
BINANCE_API_KEY=your-binance-api-key-here
BINANCE_API_SECRET=your-binance-api-secret-here

# Database (optional - uses SQLite by default)
# DATABASE_URL=sqlite:///./alphatransformer.db
```

**API Key Setup:**

1. **AI Provider API Key** (uses unified `OPENAI_API_KEY` environment variable):
   - **Default**: DeepSeek API - Get key at: https://platform.deepseek.com/api-keys
   - **To switch providers**: Modify `backend/config/agent.yaml`:
     ```yaml
     agent:
       model_name: "deepseek-chat"  # Change to: gpt-4o, claude-3-5-sonnet, etc.
       base_url: "https://api.deepseek.com/v1"  # Update base_url accordingly
       api_key: "${OPENAI_API_KEY}"
     ```

2. **Binance API**: 
   - **Register Binance**: https://accounts.maxweb.red/register?ref=899414088 (Use referral for cashback)
   - Go to Binance Futures → API Management
   - Create API key with "Enable Futures" permission
   - ⚠️ **Important**: Enable "Permit Universal Transfer" if using real trading
   - For testing: Use Binance Testnet (testnet.binancefuture.com)
   - ❗ **Currently supports Binance Futures only**, submit Issue for other exchanges

**Note**: The system automatically reads environment variables from .env file and replaces ${VAR_NAME} placeholders in config files.

### 5. Configure Agent
Edit `backend/config/agent.yaml` to customize:
- AI provider settings (model_name, base_url, api_key)
- Trading symbols
- Risk parameters
- Decision intervals

Example:
```yaml
agent:
  model_name: "gpt-4o"  # or "deepseek-chat", "claude-3-5-sonnet"
  base_url: null  # or "https://api.deepseek.com/v1" for DeepSeek
  api_key: "${OPENAI_API_KEY}"  # or "${DEEPSEEK_API_KEY}"
  decision_interval: 180
  symbols:
    - BTCUSDT
    - ETHUSDT

default_risk:
  max_position_size_percent: 0.1
  max_daily_loss_percent: 0.05
```

## Running the System

### 1. Database Setup
```bash
# SQLite database is created automatically on first run
# No manual setup required
```

### 2. Start the Trading Agent
```bash
cd backend
uv run python main.py
```

The agent will:
1. Connect to market data feeds
2. Start making trading decisions every 60 seconds
3. Execute trades through Binance Futures
4. Log all decisions and executions

### 3. Start Frontend Dashboard
```bash
# In another terminal
cd frontend
pnpm run dev
```

## Monitoring

### Web Dashboard
Access the dashboard at: `http://localhost:3000`

Features:
- Real-time position monitoring
- Decision history and reasoning
- Performance metrics
- Account snapshots

### API Endpoints
```bash
# Get account data
curl http://localhost:8000/api/account

# Get P&L history
curl http://localhost:8000/api/pnl

# Get position data
curl http://localhost:8000/api/positions

# Get agent analysis
curl http://localhost:8000/api/analysis
```

## Configuration

### Agent Prompt Customization
Modify the `system_prompt` in `config/agent.yaml` to change the agent's behavior:

```yaml
agent:
  system_prompt: |
    You are a conservative crypto trader focused on capital preservation.
    Only take high-probability trades with risk/reward ratio > 3:1.
    Always respect position size limits and stop-loss rules.
```

### Risk Management
Adjust risk parameters in the configuration:

```yaml
default_risk:
  max_position_size_percent: 0.05  # 5% per position
  max_daily_loss_percent: 0.03      # 3% daily max loss
  stop_loss_percent: 0.015          # 1.5% stop loss
```

### Trading Symbols
Add or remove symbols from the trading list:

```yaml
agent:
  symbols:
    - BTCUSDT
    - ETHUSDT
    - SOLUSDT
    - ADAUSDT
```

## Safety Features

### Paper Trading Mode
For testing, enable paper trading in the configuration:

```yaml
exchange:
  testnet: true  # Use Binance testnet
```

### Risk Controls
The system includes multiple safety layers:
- Position size limits
- Daily loss limits
- Stop-loss enforcement
- Emergency stop mechanisms

### Monitoring Alerts
Configure alerts for important events:

```yaml
logging:
  level: "INFO"
  save_decisions: true
  save_executions: true
```

## Troubleshooting

### Common Issues

**Agent not making decisions:**
- Check API credentials in .env file
- Verify OpenAI API key is valid
- Check market data connection

**Orders failing:**
- Verify Binance API permissions
- Check account balance
- Review risk limit settings

**Database connection errors:**
- Check DATABASE_URL in .env
- Ensure the database file path is writable
- Run database initialization if first time setup

### Debug Mode
Enable debug logging in `backend/config/agent.yaml`:

```yaml
logging:
  level: "DEBUG"
  save_decisions: true
  save_executions: true
```

## Next Steps

1. **Test with Paper Trading**: Always start with testnet to validate your configuration
2. **Monitor Performance**: Review decision quality and execution results
3. **Adjust Parameters**: Fine-tune risk parameters based on performance
4. **Scale Gradually**: Start with small position sizes

## Support

- Review logs in `logs/` directory
- Check API documentation at `http://localhost:8000/docs`
- Monitor real-time data in the dashboard

## Important Notes

⚠️ **Risk Warning**: This is an automated trading system. Start with small amounts and paper trading mode.

⚠️ **Market Risk**: Cryptocurrency markets are highly volatile. Only trade what you can afford to lose.

⚠️ **API Limits**: Monitor your API usage to avoid rate limiting issues.