# Quick Start: User Custom Prompt System

**Feature**: Custom Prompt System | **Date**: 2025-11-13 | **Branch**: `002-custom-prompts`

## Overview

This feature allows users to create custom prompts that personalize how the AI agent analyzes trading data. Instead of using only system defaults, users can specify their own analysis strategies and focus areas.

## Prerequisites

- AlphaTransformer system running (backend + frontend)
- Database migrations applied
- Python 3.11+ with dependencies installed

## 5-Minute Setup

### 1. Apply Database Migration

```bash
# Navigate to backend directory
cd backend/

# Run database migration
alembic upgrade head

# Verify table creation
sqlite3 data/trading.db ".schema custom_prompts"
```

### 2. Start the System

```bash
# Backend (terminal 1)
cd backend/
python -m uvicorn api.main:app --reload --port 8000

# Frontend (terminal 2)  
cd frontend/
npm run dev
```

### 3. Access Custom Prompts

1. Open browser: `http://localhost:3000`
2. Navigate to Settings (new button in navigation)
3. Go to "Custom Prompts" section

## Basic Usage

### Creating Your First Custom Prompt

1. **Click "New Prompt"** in the Custom Prompts section
2. **Fill out the form**:
   - **Title**: "Conservative Trading Strategy"
   - **Content**: 
     ```
     Focus on conservative trading approaches with emphasis on:
     - Risk management and capital preservation
     - Strong support/resistance levels
     - Multiple confirmation signals before entry
     - Conservative position sizing (max 2% account risk)
     - Clear stop-loss levels below recent swing lows
     
     Prioritize probability over profit in all analysis.
     ```
   - **Type**: "analysis" (default)

3. **Save the prompt** - it will appear in your prompt library
4. **Activate the prompt** by clicking the "Activate" button
5. **Verify activation** - the prompt should show as "Active" with green indicator

### Using Your Custom Prompt

1. **Trigger an analysis** by clicking "Run Analysis" on the dashboard
2. **Wait for completion** - the agent will use your custom prompt instead of the system default
3. **Review results** - notice how the analysis focuses on your specified criteria (conservative approach, risk management, etc.)

### Managing Prompts

**View All Prompts**: See list of all your custom prompts with status indicators
**Switch Between Prompts**: Click "Activate" on any prompt to make it active
**Edit Prompts**: Click "Edit" to modify title or content
**Delete Prompts**: Click "Delete" to permanently remove (with confirmation)

## API Usage (Advanced)

### Create Prompt via API

```bash
curl -X POST "http://localhost:8000/prompts" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Scalping Strategy",
    "content": "Focus on 1-5 minute timeframes with tight spreads and high liquidity...",
    "prompt_type": "analysis"
  }'
```

### Get Active Prompt

```bash
curl "http://localhost:8000/prompts/active/analysis"
```

### Activate Prompt

```bash
curl -X PUT "http://localhost:8000/prompts/1/activate" \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}'
```

## Example Prompt Templates

### Risk-Averse Strategy
```
Analyze market conditions with extreme caution:
- Only recommend trades with 3:1 risk/reward minimum
- Require multiple timeframe confirmation
- Focus on major support/resistance levels
- Avoid trading during high volatility news events
- Maximum position size: 1% of account
- Always include stop-loss recommendations
```

### Growth-Focused Strategy  
```
Identify high-growth trading opportunities:
- Look for breakout patterns from consolidation
- Focus on trending markets with strong momentum
- Analyze volume confirmation on price moves
- Consider higher risk/reward ratios (2:1 minimum)
- Position sizing based on volatility (2-5% account risk)
- Include both short-term and swing trade setups
```

### Technical Analysis Focus
```
Provide detailed technical analysis covering:
- Key support and resistance levels
- Moving average analysis (20, 50, 200 EMA)
- RSI divergences and overbought/oversold conditions
- Volume analysis and confirmation signals
- Chart pattern recognition (triangles, flags, head and shoulders)
- Fibonacci retracement levels
- Market structure analysis (higher highs, lower lows)
```

## Troubleshooting

### Prompt Not Being Used
- **Check activation**: Ensure prompt shows "Active" status in the UI
- **Verify API**: Call `GET /prompts/active/analysis` to confirm active prompt
- **Restart agent**: If needed, restart the backend service to refresh prompt cache

### Analysis Errors
- **Check prompt content**: Ensure no special characters that might break LLM processing
- **Test with default**: Deactivate custom prompt to see if analysis works with system default
- **Check logs**: Review backend logs for prompt-related errors

### Database Issues
- **Migration failed**: Run `alembic current` to check migration status
- **Table missing**: Verify `custom_prompts` table exists in SQLite database
- **Permissions**: Ensure write access to `backend/data/trading.db`

### Frontend Issues
- **Settings page not found**: Clear browser cache and refresh
- **API errors**: Check if backend is running on port 8000
- **Form validation**: Ensure prompt title and content are not empty

## What's Next

### Immediate Actions
1. **Create 2-3 different prompts** for different market conditions
2. **Test prompt switching** by activating different prompts and comparing analysis results  
3. **Monitor performance** over several analysis cycles to see impact

### Advanced Usage
1. **A/B testing**: Compare analysis quality between different prompts
2. **Market-specific prompts**: Create prompts tailored to specific trading pairs or market conditions
3. **Backtesting**: Use historical data to evaluate prompt effectiveness

### Future Enhancements (Not in this release)
- Prompt versioning and history
- Community prompt sharing
- Performance metrics per prompt
- Automated prompt optimization suggestions

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review backend logs in terminal where uvicorn is running
3. Check browser console for frontend errors
4. Verify database connectivity and permissions

For development questions, refer to the implementation plan and API contracts in this spec directory.