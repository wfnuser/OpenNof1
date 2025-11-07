// API Response Types
export interface AccountValue {
  timestamp: string;
  value: number;
}

export interface TradeAction {
  action: 'OPEN_LONG' | 'OPEN_SHORT' | 'CLOSE_LONG' | 'CLOSE_SHORT' | 'HOLD';
  symbol: string;
  quantity?: number;
  price?: number;
  pnl?: number;
  holdingTime?: string;
}

export interface Decision {
  id: string; // analysis_id (UUID)
  sequence: number; // numeric database id, newer decisions have larger numbers
  timestamp: string;
  reasoning: string;
  actions: TradeAction[]; // Multiple actions per cycle
  status: 'PENDING' | 'EXECUTED' | 'CANCELLED' | 'FAILED';
}

export interface Position {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  leverage: number;
  notional: number;
  unrealizedPnl: number;
  timestamp: string;
}

export interface TradeStats {
  totalTrades: number;
  totalVolume: number;
  totalPnl: number;
  totalPnlPercent: number;
  winRate: number;
  avgTradeSize: number;
  maxDrawdown: number;
  sharpeRatio: number;
}

// Component Props
export interface AccountChartProps {
  data: AccountValue[];
}

export interface DecisionsListProps {
  decisions: Decision[];
  onLoadMore?: () => void;
  hasMore?: boolean;
  isLoadingMore?: boolean;
}

export interface PositionsListProps {
  positions: Position[];
}

export interface StatsCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'positive' | 'negative' | 'neutral';
}
