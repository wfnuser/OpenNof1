'use client';

import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import AccountChart from '@/components/charts/AccountChart';
import DecisionsList from '@/components/trading/DecisionsList';
import PositionsList from '@/components/trading/PositionsList';
import StatsCard from '@/components/stats/StatsCard';
import { formatNumber } from '@/lib/utils';
import { fetchAccountData, fetchDecisions, fetchPositions, fetchStats } from '@/lib/api';
import type { AccountValue, Decision, Position, TradeStats } from '@/lib/types';

export default function TradingDashboard() {
  const [accountData, setAccountData] = useState<AccountValue[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [stats, setStats] = useState<TradeStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async (isInitial = false) => {
      try {
        if (isInitial) {
          setLoading(true);
        }
        const [accountDataResult, decisionsResult, positionsResult, statsResult] = await Promise.all([
          fetchAccountData(),
          fetchDecisions(),
          fetchPositions(),
          fetchStats()
        ]);

        setAccountData(accountDataResult);
        setDecisions(decisionsResult);
        setPositions(positionsResult);
        setStats(statsResult);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        if (isInitial) {
          setLoading(false);
        }
      }
    };

    // Initial load with loading state
    loadData(true);

    // Set up periodic data refresh (without loading state)
    const interval = setInterval(() => loadData(false), 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

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
      <header className="bg-white border-b-2 border-black px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold uppercase tracking-wider">Alpha TRANSFORMER</h1>
            <div className="text-sm text-muted-foreground">AI Trading Dashboard</div>
          </div>
          <div className="text-sm font-medium">
            Live Trading • {new Date().toLocaleDateString()}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 min-h-0">
        {/* Left Side - Chart and Bottom Stats */}
        <div className="flex-1 flex flex-col">
          {/* Chart Area */}
          <div className="flex-1 p-6 min-h-0">
            <AccountChart data={accountData} />
          </div>
          
          {/* Bottom Stats Area */}
          <div className="border-t-2 border-black bg-white flex-shrink-0">
            <div className="grid grid-cols-5">
              {/* TOTAL TRADES */}
              <div className="border-r-2 border-black p-4 flex flex-col justify-center text-center">
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-2">TOTAL TRADES</div>
                <div className="text-xl font-bold font-mono">{stats.totalTrades}</div>
              </div>
              
              {/* WIN RATE */}
              <div className="border-r-2 border-black p-4 flex flex-col justify-center text-center">
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-2">WIN RATE</div>
                <div className="text-xl font-bold font-mono text-green-600">{stats.winRate}%</div>
              </div>
              
              {/* TOTAL P&L */}
              <div className="border-r-2 border-black p-4 flex flex-col justify-center text-center">
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-2">TOTAL P&L</div>
                <div className={`text-xl font-bold font-mono ${stats.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatNumber(stats.totalPnl)}
                </div>
              </div>
              
              {/* TOTAL VOLUME */}
              <div className="border-r-2 border-black p-4 flex flex-col justify-center text-center">
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-2">TOTAL VOLUME</div>
                <div className="text-xl font-bold font-mono">{formatNumber(stats.totalVolume)}</div>
              </div>
              
              {/* ACTIVE POSITIONS */}
              <div className="p-4 flex flex-col justify-center text-center">
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono mb-2">ACTIVE POSITIONS</div>
                <div className="text-xl font-bold font-mono">{positions.length}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Sidebar */}
        <div className="w-[500px] border-l-2 border-black bg-white flex-shrink-0">
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
              <DecisionsList decisions={decisions} />
            </TabsContent>
            
            <TabsContent value="positions" className="mt-0 flex-1 min-h-0">
              <PositionsList positions={positions} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}