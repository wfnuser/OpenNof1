import type { AccountValue, Decision, Position, TradeStats } from './types';
import { getApiBaseUrl } from './config';

// Dynamic API base URL based on configuration
const API_BASE_URL = getApiBaseUrl();

// Error handling utility
class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

// Generic fetch wrapper with error handling
async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      let errorMessage = `API request failed: ${response.status} ${response.statusText}`;

      try {
        const data = await response.json();
        if (data && typeof data === 'object' && typeof (data as any).message === 'string') {
          errorMessage = (data as any).message;
        }
      } catch (jsonError) {
        // Non-JSON response, keep default message
      }

      throw new ApiError(errorMessage, response.status);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Handle network errors
    console.error('API request failed:', error);
    throw new ApiError('Network error - unable to connect to trading system');
  }
}

// API Response type mappings
interface BackendBalanceHistory {
  timestamp: string;
  value: number;
}

interface BackendDecisionResponse {
  id: number;
  timestamp: string;
  analysis_id: string;
  overall_summary?: string;
  symbol_decisions: Record<string, {
    action: string;
    reasoning: string;
    execution_status: string;
    execution_result?: {
      status: string;
      action: string;
      symbol: string;
      message: string;
      quantity?: number;
      price?: number;
      timestamp: string;
    };
  }>;
  model_name: string;
  duration_ms?: number;
}

interface BackendPosition {
  symbol: string;
  side: string;
  size: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
  percentage_pnl: number;
  leverage: number;
  margin: number;
  timestamp: string;
}

interface BackendTradeStats {
  totalTrades: number;
  totalVolume: number;
  totalPnl: number;
  totalPnlPercent: number;
  winRate: number;
  avgTradeSize: number;
  maxDrawdown: number;
  sharpeRatio: number;
  activePositions: number;
}

// Agent control/monitoring response types
export interface AgentStatus {
  is_running: boolean;
  decision_interval: number;
  symbols: string[];
  timeframes: string[];
  model_name: string;
  last_run?: string | null;
  next_run?: string | null;
  uptime_seconds?: number | null;
}

export interface AgentControlResponse {
  success: boolean;
  message: string;
  timestamp: string;
}

// Data transformation utilities
function transformDecisionData(backendDecision: BackendDecisionResponse): Decision {
  const actions = Object.entries(backendDecision.symbol_decisions).map(([symbol, decision]) => ({
    action: decision.action as any,
    symbol,
    quantity: decision.execution_result?.quantity,
    price: decision.execution_result?.price,
    // Note: Backend doesn't provide pnl and holdingTime in this format
    // These might need to be calculated or fetched separately
  }));

  return {
    id: backendDecision.analysis_id,
    sequence: backendDecision.id,
    timestamp: backendDecision.timestamp,
    reasoning: backendDecision.overall_summary || 'AI analysis completed',
    actions,
    status: 'EXECUTED', // Backend decisions are typically executed
  };
}

function transformPositionData(backendPosition: BackendPosition): Position {
  return {
    id: `${backendPosition.symbol}-${backendPosition.side}`, // Generate ID
    symbol: backendPosition.symbol,
    side: backendPosition.side as 'LONG' | 'SHORT',
    leverage: backendPosition.leverage,
    notional: backendPosition.size * backendPosition.mark_price, // Calculate notional
    unrealizedPnl: backendPosition.unrealized_pnl,
    timestamp: backendPosition.timestamp,
  };
}

interface FetchAccountDataOptions {
  days?: number;
  includeAll?: boolean;
}

interface FetchDecisionsOptions {
  limit?: number;
  offset?: number;
  order?: 'asc' | 'desc';
}

// API Functions - Via Next.js API Routes  
export async function fetchAccountData(options: FetchAccountDataOptions = {}): Promise<AccountValue[]> {
  try {
    const params = new URLSearchParams();
    if (options.includeAll) {
      params.set('include_all', 'true');
    } else if (options.days !== undefined) {
      params.set('days', String(options.days));
    }

    const query = params.toString();
    const endpoint = `/trading/balance/history${query ? `?${query}` : ''}`;
    const balanceHistory = await apiRequest<BackendBalanceHistory[]>(endpoint);
    
    return balanceHistory.map(item => ({
      timestamp: item.timestamp,
      value: item.value
    }));
  } catch (error) {
    console.error('Failed to fetch account data:', error);
    // Return empty array if API fails
    return [];
  }
}

export async function fetchDecisions(options: FetchDecisionsOptions = {}): Promise<Decision[]> {
  try {
    const limit = options.limit ?? 20;
    const order = options.order ?? 'desc';
    const params = new URLSearchParams({ limit: String(limit), order });
    if (options.offset !== undefined) {
      params.set('offset', String(options.offset));
    }

    const endpoint = `/decisions?${params.toString()}`;
    const decisions = await apiRequest<BackendDecisionResponse[]>(endpoint);
    
    // Ensure decisions are sorted by timestamp descending (newest first)
    const transformedDecisions = decisions
      .map(transformDecisionData)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    
    return transformedDecisions;
  } catch (error) {
    console.error('Failed to fetch decisions:', error);
    // Return empty array if API fails
    return [];
  }
}

export async function fetchPositions(): Promise<Position[]> {
  try {
    const positions = await apiRequest<BackendPosition[]>('/trading/positions');
    
    return positions.map(transformPositionData);
  } catch (error) {
    console.error('Failed to fetch positions:', error);
    // Return empty array if API fails
    return [];
  }
}

export async function fetchStats(): Promise<TradeStats> {
  try {
    const stats = await apiRequest<BackendTradeStats>('/trading/stats?days=30');
    
    return {
      totalTrades: stats.totalTrades,
      totalVolume: stats.totalVolume,
      totalPnl: stats.totalPnl,
      totalPnlPercent: stats.totalPnlPercent,
      winRate: stats.winRate,
      avgTradeSize: stats.avgTradeSize,
      maxDrawdown: stats.maxDrawdown,
      sharpeRatio: stats.sharpeRatio,
    };
  } catch (error) {
    console.error('Failed to fetch trading stats:', error);
    // Return default stats if API fails
    return {
      totalTrades: 0,
      totalVolume: 0,
      totalPnl: 0,
      totalPnlPercent: 0,
      winRate: 0,
      avgTradeSize: 0,
      maxDrawdown: 0,
      sharpeRatio: 0,
    };
  }
}

// Additional API functions for system monitoring
export async function fetchSystemHealth() {
  return apiRequest('/health');
}

export async function fetchAgentStatus(): Promise<AgentStatus> {
  return apiRequest<AgentStatus>('/agent/status');
}

export async function startAgent(): Promise<AgentControlResponse> {
  return apiRequest<AgentControlResponse>('/agent/start', { method: 'POST' });
}

export async function stopAgent(): Promise<AgentControlResponse> {
  return apiRequest<AgentControlResponse>('/agent/stop', { method: 'POST' });
}

// Trading Strategy API types
interface TradingStrategyResponse {
  strategy: string;
}

interface TradingStrategyUpdateResponse {
  success: boolean;
  message: string;
  timestamp: string;
}

// Trading Strategy API functions
export async function fetchTradingStrategy(): Promise<TradingStrategyResponse> {
  return apiRequest<TradingStrategyResponse>('/trading/strategy');
}

export async function updateTradingStrategy(strategy: string): Promise<TradingStrategyUpdateResponse> {
  return apiRequest<TradingStrategyUpdateResponse>('/trading/strategy', {
    method: 'POST',
    body: JSON.stringify({ strategy }),
  });
}

export async function resetTradingStrategy(): Promise<TradingStrategyUpdateResponse> {
  return apiRequest<TradingStrategyUpdateResponse>('/trading/strategy', {
    method: 'DELETE',
  });
}

// Utility function to create real-time data updates
export function createDataStream<T>(
  fetchFn: () => Promise<T>,
  interval: number = 30000 // 30 seconds default
): () => void {
  const intervalId = setInterval(fetchFn, interval);
  return () => clearInterval(intervalId);
}

// Mock data generators (keep for fallback/testing)
export const generateMockAccountData = (days: number = 30): AccountValue[] => {
  const data: AccountValue[] = [];
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  
  let value = 10000;
  
  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    
    const dailyReturn = (Math.random() - 0.48) * 0.02;
    value *= (1 + dailyReturn);
    
    data.push({
      timestamp: date.toISOString(),
      value: Math.max(value, 1000)
    });
  }
  
  return data;
};
