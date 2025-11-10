'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import AccountChart from '@/components/charts/AccountChart';
import DecisionsList from '@/components/trading/DecisionsList';
import PositionsList from '@/components/trading/PositionsList';
import StatsCard from '@/components/stats/StatsCard';
import { formatNumber } from '@/lib/utils';
import { fetchAccountData, fetchDecisions, fetchPositions, fetchStats } from '@/lib/api';
import type { AccountValue, Decision, Position, TradeStats } from '@/lib/types';
import { Twitter, Github } from 'lucide-react';

const DECISIONS_PAGE_SIZE = 20;

export default function TradingDashboard() {
  const [accountData, setAccountData] = useState<AccountValue[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [stats, setStats] = useState<TradeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [hasMoreDecisions, setHasMoreDecisions] = useState(true);
  const [isLoadingMoreDecisions, setIsLoadingMoreDecisions] = useState(false);
  const loadData = useCallback(async (isInitial = false) => {
    try {
      if (isInitial) {
        setLoading(true);
      }

      setError(null);
      setIsOffline(false);

      const [accountDataResult, decisionsResult, positionsResult, statsResult] = await Promise.all([
        fetchAccountData({ includeAll: true }),
        fetchDecisions({ limit: DECISIONS_PAGE_SIZE, offset: 0 }),
        fetchPositions(),
        fetchStats()
      ]);

      setAccountData(accountDataResult);
      setPositions(positionsResult);
      setStats(statsResult);

      setDecisions((prev) => {
        if (isInitial || prev.length === 0) {
          setHasMoreDecisions(decisionsResult.length === DECISIONS_PAGE_SIZE);
          return decisionsResult;
        }

        const latestIds = new Set(decisionsResult.map((decision) => decision.id));
        return decisionsResult.concat(
          prev.filter((decision) => !latestIds.has(decision.id))
        );
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to load data';
      setError(errorMessage);
      setIsOffline(true);

      if (isInitial) {
        setStats({
          totalTrades: 0,
          totalVolume: 0,
          totalPnl: 0,
          totalPnlPercent: 0,
          winRate: 0,
          avgTradeSize: 0,
          maxDrawdown: 0,
          sharpeRatio: 0,
        });
      }
    } finally {
      if (isInitial) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadData(true);
    const interval = setInterval(() => loadData(false), 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleLoadMoreDecisions = useCallback(async () => {
    if (isLoadingMoreDecisions || !hasMoreDecisions) {
      return;
    }

    setIsLoadingMoreDecisions(true);
    try {
      const nextPage = await fetchDecisions({
        limit: DECISIONS_PAGE_SIZE,
        offset: decisions.length,
      });

      setDecisions((prev) => {
        const existingIds = new Set(prev.map((decision) => decision.id));
        const filtered = nextPage.filter((decision) => !existingIds.has(decision.id));
        return [...prev, ...filtered];
      });

      if (nextPage.length < DECISIONS_PAGE_SIZE) {
        setHasMoreDecisions(false);
      }
    } catch (error) {
      console.error('Failed to load more decisions:', error);
    } finally {
      setIsLoadingMoreDecisions(false);
    }
  }, [decisions.length, hasMoreDecisions, isLoadingMoreDecisions]);

  const currentAccountValue = accountData[accountData.length - 1]?.value || 10000;

  if (loading) {
    return (
      <div className="min-h-screen bg-white font-mono flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold mb-2">ALPHA TRANSFORMER</div>
          <div className="text-sm text-muted-foreground">Loading trading data...</div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="min-h-screen bg-white font-mono flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold mb-2">ALPHA TRANSFORMER</div>
          <div className="text-sm text-red-600">Failed to load trading data</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-white font-mono flex flex-col">
      {/* Header */}
      <header className="bg-white border-b-2 border-black px-4 md:px-6 py-3 md:py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 md:space-x-4">
            <h1 className="text-lg md:text-xl font-bold uppercase tracking-wider">Alpha TRANSFORMER</h1>
            <div className="hidden md:block text-sm text-muted-foreground">Your AI Trading Dashboard</div>
          </div>
          <div className="flex items-center space-x-2 md:space-x-3">
            <div className="text-xs md:text-sm font-medium flex items-center space-x-1 md:space-x-2">
              <div className={`w-2 h-2 rounded-full ${isOffline ? 'bg-red-500' : 'bg-green-500'}`} />
              <span className="hidden sm:inline">{isOffline ? 'Offline' : 'Live Trading'} • </span>
              <span className="hidden md:inline">{new Date().toLocaleDateString()}</span>
              {error && (
                <span className="text-red-600 text-xs ml-1 md:ml-2" title={error}>
                  Error
                </span>
              )}
            </div>
            <div className="flex items-center space-x-1">
              <a 
                href="https://twitter.com/intent/follow?screen_name=weiraolilun" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-center w-7 h-7 md:w-8 md:h-8 hover:bg-gray-100 rounded-full transition-colors duration-200"
                title="Tend to follow"
              >
                <Twitter size={16} className="md:w-[18px] md:h-[18px] text-gray-700 hover:text-black" />
              </a>
              <a 
                href="https://github.com/wfnuser/OpenNof1" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-center w-7 h-7 md:w-8 md:h-8 hover:bg-gray-100 rounded-full transition-colors duration-200"
                title="View GitHub profile"
              >
                <Github size={16} className="md:w-[18px] md:h-[18px] text-gray-700 hover:text-black" />
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-col flex-1 min-h-0">
        {/* Chart and Stats Section - Always visible */}
        <div className="lg:flex lg:flex-row lg:flex-1 lg:min-h-0">
          {/* Chart Area */}
          <div className="lg:flex-1 lg:flex lg:flex-col lg:min-h-0">
            <div className="h-48 sm:h-64 lg:flex-1 p-2 sm:p-3 md:p-4 lg:min-h-0">
              <AccountChart data={accountData} />
            </div>
            
            {/* Bottom Stats Area */}
            <div className="border-t-2 border-black bg-white flex-shrink-0">
              <div className="grid grid-cols-3 sm:grid-cols-5">
                {/* TOTAL TRADES */}
                <div className="border-r-2 border-black p-2 md:p-4 flex flex-col justify-center text-center">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-1 md:mb-2">TRADES</div>
                  <div className="text-base md:text-xl font-bold font-mono">{stats.totalTrades}</div>
                </div>
                
                {/* TOTAL VOLUME - Visible on mobile, replaces WIN RATE */}
                <div className="border-r-2 border-black p-2 md:p-4 flex flex-col justify-center text-center sm:hidden">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-1 md:mb-2">VOLUME</div>
                  <div className="text-base md:text-xl font-bold font-mono">{formatNumber(stats.totalVolume)}</div>
                </div>
                
                {/* WIN RATE - Hidden on mobile */}
                <div className="hidden sm:block border-r-2 border-black p-2 md:p-4 flex flex-col justify-center text-center">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-1 md:mb-2">WIN RATE</div>
                  <div className="text-base md:text-xl font-bold font-mono text-green-600">{stats.winRate}%</div>
                </div>
                
                {/* TOTAL P&L */}
                <div className="p-2 md:p-4 flex flex-col justify-center text-center sm:border-r-2 sm:border-black">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-1 md:mb-2">P&L</div>
                  <div className={`text-base md:text-xl font-bold font-mono ${stats.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatNumber(stats.totalPnl)}
                  </div>
                </div>
                
                {/* TOTAL VOLUME - Desktop version */}
                <div className="hidden sm:block border-r-2 border-black p-2 md:p-4 flex flex-col justify-center text-center">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-1 md:mb-2">VOLUME</div>
                  <div className="text-base md:text-xl font-bold font-mono">{formatNumber(stats.totalVolume)}</div>
                </div>
                
                {/* ACTIVE POSITIONS - Hidden on small screens */}
                <div className="hidden sm:block p-2 md:p-4 flex flex-col justify-center text-center">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-1 md:mb-2">POSITIONS</div>
                  <div className="text-base md:text-xl font-bold font-mono">{positions.length}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Decisions/Positions Section - Sidebar on desktop only */}
          <div className="hidden lg:block lg:w-[500px] lg:border-l-2 border-black bg-white flex-shrink-0">
            <Tabs defaultValue="positions" className="h-full flex flex-col">
              <TabsList className="grid w-full grid-cols-2 rounded-none border-b-2 border-black bg-white p-0 flex-shrink-0 h-12">
                <TabsTrigger 
                  value="decisions" 
                  className="rounded-none border-r border-black data-[state=active]:bg-black data-[state=active]:text-white bg-white text-black font-mono text-sm uppercase tracking-wider h-full m-0 border-0"
                >
                  DECISIONS
                </TabsTrigger>
                <TabsTrigger 
                  value="positions" 
                  className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white bg-white text-black font-mono text-sm uppercase tracking-wider h-full m-0 border-0"
                >
                  POSITIONS
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="decisions" className="mt-0 flex-1 min-h-0">
                <DecisionsList 
                  decisions={decisions} 
                  onLoadMore={handleLoadMoreDecisions}
                  hasMore={hasMoreDecisions}
                  isLoadingMore={isLoadingMoreDecisions}
                />
              </TabsContent>
              
              <TabsContent value="positions" className="mt-0 flex-1 min-h-0">
                <PositionsList positions={positions} />
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Mobile Decisions/Positions Section */}
        <div className="lg:hidden border-t-2 border-black bg-white flex-shrink-0">
          <Tabs defaultValue="positions" className="flex flex-col h-80">
            <TabsList className="grid w-full grid-cols-2 rounded-none border-b-2 border-black bg-white p-0 flex-shrink-0 h-10">
              <TabsTrigger 
                value="decisions" 
                className="rounded-none border-r border-black data-[state=active]:bg-black data-[state=active]:text-white bg-white text-black font-mono text-xs uppercase tracking-wider h-full m-0 border-0"
              >
                DECISIONS
              </TabsTrigger>
              <TabsTrigger 
                value="positions" 
                className="rounded-none data-[state=active]:bg-black data-[state=active]:text-white bg-white text-black font-mono text-xs uppercase tracking-wider h-full m-0 border-0"
              >
                POSITIONS
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="decisions" className="mt-0 flex-1 overflow-y-auto">
              <DecisionsList 
                decisions={decisions} 
                onLoadMore={handleLoadMoreDecisions}
                hasMore={hasMoreDecisions}
                isLoadingMore={isLoadingMoreDecisions}
              />
            </TabsContent>
            
            <TabsContent value="positions" className="mt-0 flex-1 overflow-y-auto">
              <PositionsList positions={positions} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
