import React from 'react';
import type { StatsCardProps } from '@/lib/types';

const StatsCard: React.FC<StatsCardProps> = ({ 
  title, 
  value, 
  change, 
  changeType = 'neutral' 
}) => {
  const getChangeColor = () => {
    switch (changeType) {
      case 'positive':
        return 'text-green-600';
      case 'negative':
        return 'text-red-600';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded p-3">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide font-mono mb-1">
        {title}
      </div>
      <div className="text-lg font-bold font-mono text-gray-900">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      {change !== undefined && (
        <div className={`text-xs font-medium font-mono ${getChangeColor()}`}>
          {change > 0 ? '+' : ''}{change.toFixed(2)}%
        </div>
      )}
    </div>
  );
};

export default StatsCard;