import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatNumber } from '@/lib/utils';
import type { AccountChartProps } from '@/lib/types';

const AccountChart: React.FC<AccountChartProps> = ({ data }) => {
  const formatTooltipValue = (value: number) => {
    return formatNumber(value);
  };

  const formatAxisValue = (value: string) => {
    const date = new Date(value);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const currentValue = data[data.length - 1]?.value || 0;
  const initialValue = data[0]?.value || 0;
  const change = currentValue - initialValue;  // 总盈亏 (相对于初始值)
  const changePercent = initialValue !== 0 ? (change / initialValue) * 100 : 0;
  
  // 根据总盈亏情况确定线条颜色 (统一使用 Tailwind 的 green-600 和 red-600)
  const isProfit = currentValue >= initialValue;
  const lineColor = isProfit ? '#16a34a' : '#dc2626'; // green-600 : red-600
  
  // Tooltip 自定义渲染函数
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const value = payload[0].value;
      const isTooltipProfit = value >= initialValue;
      const tooltipColor = isTooltipProfit ? '#16a34a' : '#dc2626';
      
      return (
        <div style={{
          backgroundColor: '#ffffff',
          border: '1px solid #000000',
          borderRadius: '0',
          fontFamily: 'IBM Plex Mono',
          fontSize: '12px',
          padding: '8px'
        }}>
          <p style={{ margin: 0, color: '#000000' }}>
            {new Date(label).toLocaleString()}
          </p>
          <p style={{ margin: 0, color: tooltipColor, fontWeight: 'bold' }}>
            Account Value: {formatNumber(value)}
          </p>
        </div>
      );
    }
    return null;
  };

  // 自定义 activeDot 组件
  const CustomActiveDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!payload) return null;
    
    const value = payload.value;
    const isDotProfit = value >= initialValue;
    const dotColor = isDotProfit ? '#16a34a' : '#dc2626';
    
    return (
      <circle
        cx={cx}
        cy={cy}
        r={4}
        stroke={dotColor}
        strokeWidth={2}
        fill={dotColor}
      />
    );
  };

  return (
    <div className="h-full flex flex-col">
      <div className="pb-1 flex-shrink-0">
        <div className="flex flex-col space-y-1">
          <div className="text-center hidden sm:block">
            <h3 className="text-xs font-bold tracking-wider uppercase text-black">
              Total Account Value
            </h3>
          </div>
          <div className="text-center">
            <div className="text-xl sm:text-2xl font-bold text-black">
              {formatNumber(currentValue)}
            </div>
            <div className={`text-xs sm:text-sm font-medium ${
              change >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {change >= 0 ? '+' : ''}{formatNumber(change)} ({changePercent.toFixed(2)}%)
            </div>
          </div>
        </div>
      </div>
      <div className="pb-1 sm:pb-2 flex-1 min-h-0">
        <div className="h-full w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 2, right: 15, left: 15, bottom: 2 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d1d5db" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={formatAxisValue}
                tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }}
                stroke="#666666"
                height={25}
              />
              <YAxis 
                tickFormatter={(value) => {
                  if (value >= 1000000) {
                    return `$${(value / 1000000).toFixed(1)}M`;
                  } else if (value >= 1000) {
                    return `$${(value / 1000).toFixed(0)}k`;
                  } else {
                    return `$${value.toFixed(0)}`;
                  }
                }}
                tick={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }}
                stroke="#666666"
                width={50}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke={lineColor} 
                strokeWidth={2}
                dot={false}
                activeDot={<CustomActiveDot />}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default AccountChart;