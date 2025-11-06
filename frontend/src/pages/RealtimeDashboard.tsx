import React, { useState, useEffect } from 'react';

const RealtimeDashboard = () => {
    const [metrics, setMetrics] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const response = await fetch('/api/v1/dashboards/realtime-metrics');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                setMetrics(data);
            } catch (e) {
                setError(e.message);
            }
        };

        fetchMetrics();
        const interval = setInterval(fetchMetrics, 5000); // Refresh every 5 seconds

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-6 bg-gray-900 text-white min-h-screen">
            <h1 className="text-3xl font-bold mb-6">Real-time Metrics Dashboard</h1>

            {error && <div className="bg-red-500 text-white p-4 rounded mb-6">Error: {error}</div>}

            {!metrics && !error && <div>Loading metrics...</div>}

            {metrics && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Placeholder for Total Requests */}
                    <div className="bg-gray-800 p-4 rounded-lg shadow">
                        <h2 className="text-xl font-semibold mb-2">Total Requests</h2>
                        <p className="text-4xl font-bold">{metrics.requests_total.reduce((acc, curr) => acc + curr.value, 0)}</p>
                    </div>

                    {/* More metric cards will be added here */}
                </div>
            )}
        </div>
    );
};

export default RealtimeDashboard;
