
import { useState, useEffect } from 'react';

const SupabaseDashboard = () => {
    const [data, setData] = useState<any[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [tableName, setTableName] = useState('example_table'); // <-- IMPORTANT: Change this to your table name

    useEffect(() => {
        const fetchData = async () => {
            if (!tableName) return;

            try {
                const response = await fetch(`/api/v1/dashboards/supabase/${tableName}`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }
                const result = await response.json();
                setData(result);
                setError(null);
            } catch (e: any) {
                setError(e.message);
                setData(null);
            }
        };

        fetchData();
    }, [tableName]);

    return (
        <div className="p-6 bg-gray-900 text-white min-h-screen">
            <h1 className="text-3xl font-bold mb-6">Supabase Data Dashboard</h1>

            <div className="mb-4">
                <label htmlFor="tableName" className="mr-2">Enter Table Name:</label>
                <input 
                    id="tableName" 
                    type="text" 
                    value={tableName} 
                    onChange={(e) => setTableName(e.target.value)} 
                    className="bg-gray-700 text-white p-2 rounded"
                />
            </div>

            {error && <div className="bg-red-500 text-white p-4 rounded mb-6">Error: {error}</div>}

            {!data && !error && <div>Loading data from '{tableName}'...</div>}

            {data && (
                <div className="bg-gray-800 p-4 rounded-lg shadow">
                    <h2 className="text-xl font-semibold mb-4">Data from '{tableName}'</h2>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-700">
                            <thead className="bg-gray-700">
                                <tr>
                                    {data.length > 0 && Object.keys(data[0]).map((key) => (
                                        <th key={key} scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                                            {key}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="bg-gray-800 divide-y divide-gray-700">
                                {data.map((row, rowIndex) => (
                                    <tr key={rowIndex}>
                                        {Object.values(row).map((value: any, colIndex) => (
                                            <td key={colIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                                                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SupabaseDashboard;
