import { useState, useEffect } from 'react';
import { RealTimeMetrics } from '@/components/dashboard/RealTimeMetrics';
import { D3TreeMap, D3ForceGraph, D3HeatMap } from '@/components/dashboard/D3Visualizations';
import { BarChart3, Network, Activity } from 'lucide-react';

interface AIModelPerformance {
  name: string;
  accuracy: number;
  latency: number;
  requests: number;
}

export const BIDashboard = () => {
  const [activeTab, setActiveTab] = useState<'realtime' | 'treemap' | 'network' | 'heatmap'>('realtime');
  const [modelPerformance, setModelPerformance] = useState<AIModelPerformance[]>([]);

  useEffect(() => {
    // Fetch AI model performance data
    const fetchModelPerformance = async () => {
      try {
        // Mock data - replace with actual API call
        setModelPerformance([
          { name: 'LSTM Revenue', accuracy: 94.2, latency: 45, requests: 1250 },
          { name: 'Anomaly Detection', accuracy: 89.7, latency: 32, requests: 890 },
          { name: 'Recommendations', accuracy: 91.3, latency: 28, requests: 3420 },
          { name: 'Swarm Optimizer', accuracy: 88.5, latency: 156, requests: 234 },
          { name: 'AGI Framework', accuracy: 92.8, latency: 210, requests: 456 },
        ]);
      } catch (error) {
        console.error('Failed to fetch model performance:', error);
      }
    };

    fetchModelPerformance();
    const interval = setInterval(fetchModelPerformance, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, []);

  // TreeMap data for AI model usage
  const treeMapData = {
    name: 'AI Services',
    value: 0,
    children: modelPerformance.map(model => ({
      name: model.name,
      value: model.requests,
    })),
  };

  // Force graph data for service dependencies
  const forceGraphNodes = [
    { id: 'API Gateway', group: 1, value: 100 },
    { id: 'LSTM', group: 2, value: 80 },
    { id: 'AGI', group: 2, value: 90 },
    { id: 'Recommendations', group: 2, value: 120 },
    { id: 'Anomaly', group: 2, value: 70 },
    { id: 'Database', group: 3, value: 110 },
    { id: 'Cache', group: 3, value: 60 },
    { id: 'Neo4j', group: 3, value: 50 },
  ];

  const forceGraphLinks = [
    { source: 'API Gateway', target: 'LSTM', value: 10 },
    { source: 'API Gateway', target: 'AGI', value: 15 },
    { source: 'API Gateway', target: 'Recommendations', value: 20 },
    { source: 'API Gateway', target: 'Anomaly', value: 8 },
    { source: 'LSTM', target: 'Database', value: 12 },
    { source: 'AGI', target: 'Database', value: 10 },
    { source: 'AGI', target: 'Cache', value: 8 },
    { source: 'Recommendations', target: 'Neo4j', value: 15 },
    { source: 'Recommendations', target: 'Cache', value: 10 },
    { source: 'Anomaly', target: 'Database', value: 5 },
  ];

  // Heatmap data for model performance over time
  const heatMapData = [
    { x: '00:00', y: 'LSTM', value: 92.3 },
    { x: '04:00', y: 'LSTM', value: 91.8 },
    { x: '08:00', y: 'LSTM', value: 94.5 },
    { x: '12:00', y: 'LSTM', value: 93.2 },
    { x: '16:00', y: 'LSTM', value: 95.1 },
    { x: '20:00', y: 'LSTM', value: 92.7 },
    { x: '00:00', y: 'Anomaly', value: 88.1 },
    { x: '04:00', y: 'Anomaly', value: 89.4 },
    { x: '08:00', y: 'Anomaly', value: 87.9 },
    { x: '12:00', y: 'Anomaly', value: 90.2 },
    { x: '16:00', y: 'Anomaly', value: 89.7 },
    { x: '20:00', y: 'Anomaly', value: 88.5 },
    { x: '00:00', y: 'Recommendations', value: 90.5 },
    { x: '04:00', y: 'Recommendations', value: 91.2 },
    { x: '08:00', y: 'Recommendations', value: 92.8 },
    { x: '12:00', y: 'Recommendations', value: 91.3 },
    { x: '16:00', y: 'Recommendations', value: 93.4 },
    { x: '20:00', y: 'Recommendations', value: 90.9 },
    { x: '00:00', y: 'AGI', value: 91.8 },
    { x: '04:00', y: 'AGI', value: 92.5 },
    { x: '08:00', y: 'AGI', value: 93.1 },
    { x: '12:00', y: 'AGI', value: 92.8 },
    { x: '16:00', y: 'AGI', value: 94.2 },
    { x: '20:00', y: 'AGI', value: 91.5 },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Business Intelligence Dashboard</h1>
          <p className="text-gray-600 mt-2">Real-time AI/ML monitoring and analytics</p>
        </div>

        {/* Model Performance Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
          {modelPerformance.map((model) => (
            <div key={model.name} className="bg-white rounded-lg shadow-md p-4">
              <h3 className="text-sm font-medium text-gray-600 mb-2">{model.name}</h3>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Accuracy:</span>
                  <span className="font-semibold text-green-600">{model.accuracy}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Latency:</span>
                  <span className="font-semibold text-blue-600">{model.latency}ms</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Requests:</span>
                  <span className="font-semibold text-purple-600">{model.requests.toLocaleString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('realtime')}
              className={`flex items-center px-6 py-3 text-sm font-medium ${
                activeTab === 'realtime'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Activity className="w-4 h-4 mr-2" />
              Real-time Metrics
            </button>
            <button
              onClick={() => setActiveTab('treemap')}
              className={`flex items-center px-6 py-3 text-sm font-medium ${
                activeTab === 'treemap'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Service Usage
            </button>
            <button
              onClick={() => setActiveTab('network')}
              className={`flex items-center px-6 py-3 text-sm font-medium ${
                activeTab === 'network'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Network className="w-4 h-4 mr-2" />
              Service Dependencies
            </button>
            <button
              onClick={() => setActiveTab('heatmap')}
              className={`flex items-center px-6 py-3 text-sm font-medium ${
                activeTab === 'heatmap'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Activity className="w-4 h-4 mr-2" />
              Performance Heatmap
            </button>
          </div>
        </div>

        {/* Content */}
        <div>
          {activeTab === 'realtime' && <RealTimeMetrics />}
          
          {activeTab === 'treemap' && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">AI Service Usage Distribution</h2>
              <div className="flex justify-center">
                <D3TreeMap data={treeMapData} width={900} height={500} />
              </div>
            </div>
          )}
          
          {activeTab === 'network' && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Service Dependency Graph</h2>
              <div className="flex justify-center">
                <D3ForceGraph 
                  nodes={forceGraphNodes} 
                  links={forceGraphLinks} 
                  width={900} 
                  height={600} 
                />
              </div>
            </div>
          )}
          
          {activeTab === 'heatmap' && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Model Performance Over Time</h2>
              <div className="flex justify-center">
                <D3HeatMap data={heatMapData} width={900} height={400} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
