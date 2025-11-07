# Alpha Arena - AI Trading Dashboard

A modern, responsive dashboard for monitoring AI trading agent performance in real-time.

## Features

- **Real-time Account Value Chart**: Track portfolio value changes over time
- **Trading Decisions Log**: View AI trading decisions with reasoning and confidence levels
- **Open Positions**: Monitor active trading positions with P&L tracking
- **Performance Statistics**: Key trading metrics including win rate, Sharpe ratio, and drawdown
- **Responsive Design**: Optimized for desktop trading environments

## Tech Stack

- **Next.js 14**: React framework with App Router
- **React 18**: Frontend framework
- **TypeScript**: Type safety and developer experience
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Modern UI component library
- **Recharts**: Data visualization library
- **IBM Plex Mono**: Professional monospace font

## Design Inspiration

Based on the Alpha Arena design concept - a clean, professional trading interface with:
- Black and white color scheme for clarity
- Monospace typography for precision
- Clear data hierarchy and organization
- Real-time data visualization

## Getting Started

### Prerequisites

- Node.js 18+ 
- pnpm (recommended) or npm

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Start the development server:
   ```bash
   pnpm dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Build for Production

```bash
pnpm build
pnpm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── globals.css     # Global styles and themes
│   │   ├── layout.tsx      # Root layout
│   │   └── page.tsx        # Main dashboard page
│   ├── components/         # Reusable UI components
│   │   ├── ui/            # shadcn/ui components
│   │   ├── charts/        # Chart components
│   │   ├── trading/       # Trading-specific components
│   │   └── stats/         # Statistics components
│   └── lib/               # Utilities and types
│       ├── api.ts         # API functions and mock data
│       ├── types.ts       # TypeScript type definitions
│       └── utils.ts       # Utility functions
└── public/                # Static assets
```

## API Integration

Currently using mock data. To integrate with your backend API:

1. Update the `API_BASE_URL` in `src/lib/api.ts`
2. Replace mock functions with actual API calls
3. Update type definitions in `src/lib/types.ts` as needed

### Expected API Endpoints

- `GET /account/history` - Account value history
- `GET /decisions` - Trading decisions
- `GET /positions` - Current positions
- `GET /stats` - Trading statistics

## Components Overview

### AccountChart
- Line chart showing account value over time
- Built with Recharts for smooth performance
- Responsive design with custom styling

### DecisionsList
- Scrollable list of AI trading decisions
- Shows action, symbol, reasoning, and confidence
- Color-coded status badges

### PositionsList
- Current open positions
- Real-time P&L calculations
- Side (LONG/SHORT) indicators

### StatsCard
- Modular statistics display
- Supports value, change, and trend indicators
- Consistent styling across metrics

## Styling

- **Global Styles**: IBM Plex Mono font, trading-specific themes
- **Component Styles**: Tailwind CSS with custom trading dashboard classes
- **Colors**: Professional black/white scheme with accent colors
- **Typography**: Monospace for precision and readability

## Development Notes

- Uses React 18 with concurrent features
- TypeScript strict mode enabled
- ESLint and Prettier configured
- Optimized for fast development iteration
- Mock data for independent frontend development

## Deployment

The frontend can be deployed to any static hosting provider:

- **Vercel** (recommended for Next.js)
- **Netlify**
- **AWS S3 + CloudFront**
- **Docker** (see Dockerfile if available)

## Performance

- Optimized bundle size with Next.js
- Lazy loading for charts and heavy components
- Efficient re-renders with React best practices
- Responsive images and assets