# OpenNof1

[![Apache License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.0+-black.svg)](https://nextjs.org/)
[![AI Trading](https://img.shields.io/badge/AI-Trading%20Bot-orange.svg)](https://github.com/wfnuser/OpenNof1)
[![GitHub stars](https://img.shields.io/github/stars/wfnuser/OpenNof1.svg?style=social&label=Star)](https://github.com/wfnuser/OpenNof1)
[![GitHub forks](https://img.shields.io/github/forks/wfnuser/OpenNof1.svg?style=social&label=Fork)](https://github.com/wfnuser/OpenNof1)

[![Join Telegram Group](https://img.shields.io/badge/Telegram-opennof1-blue?style=flat&logo=telegram&logoColor=white)](https://t.me/opennof1)
[![Follow @weiraolilun](https://img.shields.io/badge/Follow-@weiraolilun-green?style=flat&logo=x&logoColor=white)](https://x.com/intent/follow?screen_name=weiraolilun)

> 📖 **中文文档**: [中文 README](./README_zh.md) | [快速开始](./quickstart_zh.md) | [环境配置](./ENVIRONMENT_zh.md)

AI-powered autonomous trading system with intelligent agents, real-time market data processing, and minimalist interface.

## Quick Start

```bash
# Install system dependencies (TA-Lib)
# macOS
brew install ta-lib

# Ubuntu/Debian
sudo apt-get install libta-lib-dev

# Install backend dependencies
cd backend && uv sync

# Install frontend dependencies
cd frontend && pnpm install

# Configure environment
cp backend/.env.example backend/.env
# Edit .env with your DeepSeek API key and Binance Key (defaults to DeepSeek)

# Start backend
cd backend && uv run python main.py

# Start frontend (new terminal)
cd frontend && pnpm run dev
```

Visit `http://localhost:3000` for the dashboard.

## Supported Exchanges

**Currently supports Binance Futures only**

- 🎁 **New User Bonus**: Use our referral link for cashback rewards
- 🔗 **Registration**: https://accounts.maxweb.red/register?ref=899414088

**Need other exchange support?**

- Please submit a GitHub Issue describing your requirements
- We'll develop support for other exchanges based on user demand priority

## Dashboard Preview

![AlphaTransformer Trading Dashboard](dashboard-screenshot.png)

_Live trading dashboard showing real-time P&L tracking, AI decisions, and position monitoring_

## Architecture

- **Backend**: FastAPI + SQLite + SQLAlchemy
- **Frontend**: Next.js 14.0 + TypeScript + TailwindCSS
- **AI**: Configurable providers (OpenAI, DeepSeek, Anthropic, etc.)
- **Market Data**: Binance Futures WebSocket
- **Trading**: Multi-exchange API integration

## Key Features

- **Configurable AI Providers**: Support for OpenAI, DeepSeek, Anthropic, and custom endpoints
- **Real-time Dashboard**: Live P&L tracking and position monitoring
- **Autonomous Trading**: AI-powered decision making with risk management
- **Minimalist UI**: Clean, professional interface inspired by modern trading platforms

## Documentation

- [Quick Start Guide](./quickstart.md) - Detailed setup instructions
- [Environment Setup](./ENVIRONMENT.md) - API keys and configuration

## Inspiration & References

- **[nof1.ai](https://nof1.ai)**
- **[nofx](https://github.com/NoFxAiOS/nofx)**
- **[nof0](https://github.com/wquguru/nof0)**

## Team

**[YouBet DAO](https://github.com/youbetdao)** - An organization dedicated to exploring more open and fair production relationships.

### Core Contributors

- [微扰理论](https://x.com/weiraolilun) - Core Developer
- [Ernest](https://x.com/0xErnest247) - Core Developer

## License

Apache License 2.0
