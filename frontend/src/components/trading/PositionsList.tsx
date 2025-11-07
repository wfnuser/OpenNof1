import React from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { formatNumber } from '@/lib/utils';
import type { PositionsListProps, Position } from '@/lib/types';

const PositionsList: React.FC<PositionsListProps> = ({ positions }) => {
  const formatPnl = (pnl: number) => {
    return pnl >= 0 ? `$${pnl.toFixed(2)}` : `-$${Math.abs(pnl).toFixed(2)}`;
  };

  const getPnlColor = (pnl: number) => {
    return pnl >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getSideColor = (side: Position['side']) => {
    return side === 'LONG' ? 'text-green-600' : 'text-red-600';
  };

  const getCoinIcon = (symbol: string) => {
    const coin = symbol.replace('USDT', '').replace('USD', '');
    switch (coin) {
      case 'BTC':
        return '₿';
      case 'ETH':
        return '⟠';
      case 'SOL':
        return '◎';
      case 'XRP':
        return '✕';
      case 'DOGE':
        return 'Ð';
      case 'BNB':
        return '⬢';
      default:
        return coin.charAt(0);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Table Header */}
      <div className="grid grid-cols-5 gap-4 py-2 px-6 text-xs text-gray-600 uppercase font-mono border-b border-gray-200 flex-shrink-0">
        <div>SIDE</div>
        <div>COIN</div>
        <div>LEVERAGE</div>
        <div>NOTIONAL</div>
        <div className="text-right">UNREAL P&L</div>
      </div>

      {/* Table Body */}
      <ScrollArea className="flex-1">
        <div className="space-y-1 px-6">
            {positions.map((position, index) => (
              <div 
                key={position.id}
                className={`grid grid-cols-5 gap-4 py-3 text-sm font-mono items-center ${
                  index % 2 === 0 ? 'bg-gray-50' : 'bg-white'
                }`}
              >
                {/* Side */}
                <div className={`font-bold ${getSideColor(position.side)}`}>
                  {position.side}
                </div>

                {/* Coin */}
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{getCoinIcon(position.symbol)}</span>
                  <span className="font-medium">
                    {position.symbol.replace('USDT', '').replace('USD', '')}
                  </span>
                </div>

                {/* Leverage */}
                <div className="font-medium">
                  {position.leverage}X
                </div>

                {/* Notional */}
                <div className="font-medium text-black">
                  {formatNumber(position.notional)}
                </div>

                {/* Unrealized P&L */}
                <div className={`text-right font-medium ${getPnlColor(position.unrealizedPnl)}`}>
                  {formatPnl(position.unrealizedPnl)}
                </div>
              </div>
            ))}
          
          {positions.length === 0 && (
            <div className="text-center py-8 text-gray-500 font-mono text-sm">
              No open positions
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

export default PositionsList;