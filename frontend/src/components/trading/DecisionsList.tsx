import React from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { formatNumber } from '@/lib/utils';
import type { DecisionsListProps, TradeAction } from '@/lib/types';

const DecisionsList: React.FC<DecisionsListProps> = ({ decisions }) => {
  const getActionColor = (action: TradeAction['action']) => {
    switch (action) {
      case 'OPEN_LONG':
      case 'CLOSE_SHORT':
        return 'text-green-600';
      case 'OPEN_SHORT':
      case 'CLOSE_LONG':
        return 'text-red-600';
      case 'HOLD':
        return 'text-gray-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatActionText = (action: TradeAction['action']) => {
    switch (action) {
      case 'OPEN_LONG':
        return 'Open a long trade on';
      case 'OPEN_SHORT':
        return 'Open a short trade on';
      case 'CLOSE_LONG':
        return 'Close a long trade on';
      case 'CLOSE_SHORT':
        return 'Close a short trade on';
      case 'HOLD':
        return 'Hold position on';
      default:
        return 'Action on';
    }
  };

  const getPnlColor = (pnl?: number) => {
    if (pnl === undefined) return 'text-gray-600';
    return pnl >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const formatPnl = (pnl?: number) => {
    if (pnl === undefined) return '-';
    return pnl >= 0 ? `$${pnl.toFixed(2)}` : `-$${Math.abs(pnl).toFixed(2)}`;
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

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  return (
    <div className="h-full flex flex-col">
      <ScrollArea className="flex-1">
        <div className="p-6 space-y-6">
          {decisions.map((decision, index) => (
            <div key={decision.id} className="pb-6 border-b border-gray-200 last:border-b-0 last:pb-0">
              <div className="px-2 space-y-3">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <span className="text-black font-medium text-sm font-mono">
                    Cycle #{index + 1}
                  </span>
                  <div className="text-gray-400 text-xs font-mono">
                    {formatTimestamp(decision.timestamp)}
                  </div>
                </div>

                {/* Reasoning */}
                {decision.reasoning && (
                  <div className="text-xs text-gray-600 leading-relaxed bg-gray-50 p-3 border-l-2 border-gray-200 font-mono">
                    {decision.reasoning}
                  </div>
                )}

                {/* Actions */}
                <div className="space-y-2">
                  {decision.actions.map((tradeAction, actionIndex) => (
                    <div key={actionIndex} className="flex items-center space-x-2 text-sm">
                      {tradeAction.action === 'HOLD' ? (
                        <>
                          <span className="text-gray-500">Hold position on</span>
                          <span className="text-lg">{getCoinIcon(tradeAction.symbol)}</span>
                          <span className="font-bold text-black">
                            {tradeAction.symbol.replace('USDT', '').replace('USD', '')}
                          </span>
                        </>
                      ) : (
                        <>
                          <span className="text-gray-500">
                            {tradeAction.action.includes('OPEN') ? 'Open a' : 'Close a'}
                          </span>
                          <span className={`font-bold ${getActionColor(tradeAction.action)}`}>
                            {tradeAction.action.includes('LONG') ? 'long' : 'short'}
                          </span>
                          <span className="text-gray-500">trade on</span>
                          <span className="text-lg">{getCoinIcon(tradeAction.symbol)}</span>
                          <span className="font-bold text-black">
                            {tradeAction.symbol.replace('USDT', '').replace('USD', '')}
                          </span>
                        </>
                      )}
                      {tradeAction.pnl !== undefined && (
                        <span className={`font-bold ${getPnlColor(tradeAction.pnl)} ml-2`}>
                          {formatPnl(tradeAction.pnl)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
          
          {decisions.length === 0 && (
            <div className="text-center py-8 text-gray-500 font-mono text-sm">
              No trading decisions recorded yet
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

export default DecisionsList;