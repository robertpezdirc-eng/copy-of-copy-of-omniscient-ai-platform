import { useEffect, useState } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, TrendingUp, Users, Zap } from 'lucide-react';
import { useWebSocket } from '../../hooks/useWebSocket';

interface MetricData {
  timestamp: string;
  cpu: number;
  memory: number;
  requests: number;
  latency: number;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: number;
  color: string;
}

const MetricCard = ({ title, value, icon, trend, color }: MetricCardProps) => (
  <div className={`bg-white rounded-lg shadow-md p-6 border-l-4 border-${color}-500`}>
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600 font-medium">{title}</p>
        <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        {trend !== undefined && (
          <div className={`flex items-center mt-2 text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            <TrendingUp className="w-4 h-4 mr-1" />
            <span>{trend >= 0 ? '+' : ''}{trend.toFixed(1)}%</span>
          </div>
        )}
      </div>
      <div className={`p-3 bg-${color}-100 rounded-full`}>
        {icon}
      </div>
    </div>
  </div>
);

export const RealTimeMetrics = () => {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [currentMetrics, setCurrentMetrics] = useState({
    cpu: 0,
    memory: 0,
    requests: 0,
    latency: 0,
  });

  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8080';
  const { isConnected, on, off } = useWebSocket({
    url: wsUrl,
    autoConnect: true,
  });

  useEffect(() => {
    const handleMetricsUpdate = (data: MetricData) => {
      setMetrics((prev) => {
        const updated = [...prev, data];
        // Keep only last 20 data points
        return updated.slice(-20);
      });

      setCurrentMetrics({
        cpu: data.cpu,
        memory: data.memory,
        requests: data.requests,
        latency: data.latency,
      });
    };

    on('metrics:update', handleMetricsUpdate);

    // Cleanup
    return () => {
      off('metrics:update', handleMetricsUpdate);
    };
  }, [on, off]);

  const calculateTrend = (key: keyof typeof currentMetrics): number => {
    if (metrics.length < 2) return 0;
    const recent = metrics.slice(-5);
    const avg = recent.reduce((sum, m) => sum + m[key], 0) / recent.length;
    const prev = metrics[metrics.length - 6]?.[key] || avg;
    return ((avg - prev) / prev) * 100;
  };

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="flex items-center justify-between bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full mr-3 ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
          <span className="text-sm font-medium text-gray-700">
            {isConnected ? 'Real-time Connected' : 'Disconnected'}
          </span>
        </div>
        <span className="text-xs text-gray-500">{metrics.length} data points</span>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="CPU Usage"
          value={`${currentMetrics.cpu.toFixed(1)}%`}
          icon={<Activity className="w-6 h-6 text-blue-600" />}
          trend={calculateTrend('cpu')}
          color="blue"
        />
        <MetricCard
          title="Memory"
          value={`${currentMetrics.memory.toFixed(1)}%`}
          icon={<Zap className="w-6 h-6 text-purple-600" />}
          trend={calculateTrend('memory')}
          color="purple"
        />
        <MetricCard
          title="Requests/min"
          value={currentMetrics.requests.toFixed(0)}
          icon={<Users className="w-6 h-6 text-green-600" />}
          trend={calculateTrend('requests')}
          color="green"
        />
        <MetricCard
          title="Avg Latency"
          value={`${currentMetrics.latency.toFixed(0)}ms`}
          icon={<TrendingUp className="w-6 h-6 text-orange-600" />}
          trend={calculateTrend('latency')}
          color="orange"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU & Memory Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">CPU & Memory Usage</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                fontSize={12}
              />
              <YAxis fontSize={12} />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleTimeString()}
                formatter={(value: number) => `${value.toFixed(1)}%`}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="cpu" 
                stroke="#3b82f6" 
                fill="#3b82f6" 
                fillOpacity={0.3}
                name="CPU %"
              />
              <Area 
                type="monotone" 
                dataKey="memory" 
                stroke="#a855f7" 
                fill="#a855f7" 
                fillOpacity={0.3}
                name="Memory %"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Requests & Latency Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Requests & Latency</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                fontSize={12}
              />
              <YAxis yAxisId="left" fontSize={12} />
              <YAxis yAxisId="right" orientation="right" fontSize={12} />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleTimeString()}
              />
              <Legend />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="requests" 
                stroke="#10b981" 
                strokeWidth={2}
                dot={false}
                name="Requests/min"
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="latency" 
                stroke="#f97316" 
                strokeWidth={2}
                dot={false}
                name="Latency (ms)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
