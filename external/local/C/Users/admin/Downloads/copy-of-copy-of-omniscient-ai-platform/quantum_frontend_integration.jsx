// Quantum Frontend Integration Example for OMNI Platform
// This file shows how to integrate quantum modules with the frontend

import React, { useState, useEffect } from 'react';

const QuantumPlayground = () => {
    const [selectedModule, setSelectedModule] = useState('quantum_gaming');
    const [prompt, setPrompt] = useState('');
    const [result, setResult] = useState('');
    const [loading, setLoading] = useState(false);
    const [quantumStatus, setQuantumStatus] = useState(null);

    // Available quantum modules
    const quantumModules = [
        {
            id: 'quantum_gaming',
            name: '🎮 Quantum Gaming',
            description: 'Generate innovative game ideas and mechanics',
            placeholder: 'Enter game theme or concept...',
            example: 'Ustvari idejo za igro na trampolinu za otroke'
        },
        {
            id: 'quantum_tourism',
            name: '🏔️ Quantum Tourism',
            description: 'Create amazing travel experiences and plans',
            placeholder: 'Enter destination and preferences...',
            example: 'Načrtuj vikend izlet v Ljubljano za družino'
        },
        {
            id: 'quantum_education',
            name: '📚 Quantum Education',
            description: 'Generate educational content and lesson plans',
            placeholder: 'Enter topic to learn...',
            example: 'Ustvari učni načrt za Python programiranje'
        },
        {
            id: 'quantum_business',
            name: '💼 Quantum Business',
            description: 'Develop business ideas and market analysis',
            placeholder: 'Enter industry or problem to solve...',
            example: 'Inovativna rešitev za mala podjetja v turizmu'
        },
        {
            id: 'quantum_creative',
            name: '🎨 Quantum Creative',
            description: 'Create stories, poetry, and artistic content',
            placeholder: 'Enter creative prompt...',
            example: 'Napiši kratko zgodbo o robotu, ki odkrije čustva'
        },
        {
            id: 'quantum_health',
            name: '🏃 Quantum Health',
            description: 'Generate wellness plans and nutrition guides',
            placeholder: 'Enter health goals...',
            example: '30-dnevni načrt za izgubo teže in več energije'
        },
        {
            id: 'quantum_technology',
            name: '💻 Quantum Technology',
            description: 'Generate code and system architectures',
            placeholder: 'Enter technical requirements...',
            example: 'Ustvari Python aplikacijo za sledenje fitnesa'
        }
    ];

    // Get quantum AI status on component mount
    useEffect(() => {
        checkQuantumStatus();
    }, []);

    const checkQuantumStatus = async () => {
        try {
            const response = await fetch('/api/quantum/status');
            if (response.ok) {
                const status = await response.json();
                setQuantumStatus(status);
            }
        } catch (error) {
            console.error('Failed to check quantum status:', error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!prompt.trim()) return;

        setLoading(true);
        setResult('');

        try {
            // Call quantum module through OMNI backend
            const response = await fetch('/api/quantum/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    module: selectedModule,
                    prompt: prompt,
                    model: 'gemini-2.0-flash'
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.ok) {
                    setResult(data.reply);
                } else {
                    setResult(`Error: ${data.error}`);
                }
            } else {
                setResult(`HTTP Error: ${response.status}`);
            }
        } catch (error) {
            setResult(`Network Error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const selectedModuleInfo = quantumModules.find(m => m.id === selectedModule);

    return (
        <div className="quantum-playground">
            <div className="quantum-header">
                <h2>🧠 OMNI Quantum AI Playground</h2>
                <p>Advanced AI-powered content generation with quantum optimization</p>

                {quantumStatus && (
                    <div className="quantum-status">
                        <span className={`status-indicator ${quantumStatus.connected ? 'connected' : 'disconnected'}`}>
                            {quantumStatus.connected ? '🟢' : '🔴'}
                        </span>
                        <span>Quantum AI: {quantumStatus.connected ? 'Connected' : 'Disconnected'}</span>
                        <span> | Modules: {quantumStatus.quantum_modules_available?.length || 0}</span>
                    </div>
                )}
            </div>

            <div className="quantum-interface">
                {/* Module Selection */}
                <div className="module-selection">
                    <h3>Select Quantum Module:</h3>
                    <div className="module-grid">
                        {quantumModules.map(module => (
                            <div
                                key={module.id}
                                className={`module-card ${selectedModule === module.id ? 'selected' : ''}`}
                                onClick={() => setSelectedModule(module.id)}
                            >
                                <div className="module-icon">{module.name.split(' ')[0]}</div>
                                <div className="module-info">
                                    <h4>{module.name}</h4>
                                    <p>{module.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Input Interface */}
                <div className="quantum-input">
                    <div className="module-info-display">
                        <h3>{selectedModuleInfo?.name}</h3>
                        <p>{selectedModuleInfo?.description}</p>
                        <div className="example-prompt">
                            <strong>Example:</strong> {selectedModuleInfo?.example}
                        </div>
                    </div>

                    <form onSubmit={handleSubmit}>
                        <textarea
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            placeholder={selectedModuleInfo?.placeholder || 'Enter your prompt...'}
                            rows={4}
                            disabled={loading}
                        />

                        <div className="form-controls">
                            <button
                                type="submit"
                                disabled={loading || !prompt.trim()}
                                className="quantum-submit-btn"
                            >
                                {loading ? '⏳ Generating...' : '🚀 Generate with Quantum AI'}
                            </button>

                            <button
                                type="button"
                                onClick={() => setPrompt(selectedModuleInfo?.example || '')}
                                className="example-btn"
                            >
                                📝 Use Example
                            </button>
                        </div>
                    </form>
                </div>

                {/* Results Display */}
                <div className="quantum-results">
                    <h3>Results:</h3>
                    {result && (
                        <div className="result-container">
                            <div className="result-content">
                                {result}
                            </div>
                            <div className="result-actions">
                                <button onClick={() => navigator.clipboard.writeText(result)}>
                                    📋 Copy
                                </button>
                                <button onClick={() => setResult('')}>
                                    🗑️ Clear
                                </button>
                            </div>
                        </div>
                    )}

                    {!result && !loading && (
                        <div className="empty-state">
                            <div className="empty-icon">🎯</div>
                            <p>Enter a prompt and click "Generate" to see quantum AI results</p>
                        </div>
                    )}

                    {loading && (
                        <div className="loading-state">
                            <div className="loading-spinner"></div>
                            <p>🧠 Quantum AI is generating content...</p>
                            <p className="loading-subtitle">This may take a few moments for complex requests</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Quantum Performance Metrics */}
            {quantumStatus && (
                <div className="quantum-metrics">
                    <h4>⚛️ Quantum Performance Metrics</h4>
                    <div className="metrics-grid">
                        <div className="metric">
                            <span className="metric-label">Cache Size:</span>
                            <span className="metric-value">{quantumStatus.cache_size || 0}</span>
                        </div>
                        <div className="metric">
                            <span className="metric-label">Active Modules:</span>
                            <span className="metric-value">{quantumStatus.quantum_modules_available?.length || 0}</span>
                        </div>
                        <div className="metric">
                            <span className="metric-label">API Response:</span>
                            <span className="metric-value">{quantumStatus.session_timeout || 30}s</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// CSS Styles for Quantum Playground
const quantumStyles = `
.quantum-playground {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.quantum-header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    color: white;
}

.quantum-status {
    margin-top: 10px;
    font-size: 14px;
    opacity: 0.9;
}

.status-indicator {
    margin-right: 5px;
    font-size: 16px;
}

.module-selection {
    margin-bottom: 30px;
}

.module-selection h3 {
    margin-bottom: 15px;
    color: #333;
}

.module-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
}

.module-card {
    padding: 15px;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
}

.module-card:hover {
    border-color: #667eea;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.module-card.selected {
    border-color: #667eea;
    background-color: #f8f9ff;
}

.module-icon {
    font-size: 24px;
    margin-right: 15px;
}

.module-info h4 {
    margin: 0 0 5px 0;
    color: #333;
}

.module-info p {
    margin: 0;
    font-size: 12px;
    color: #666;
}

.quantum-input {
    background: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

.module-info-display {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #eee;
}

.module-info-display h3 {
    margin: 0 0 5px 0;
    color: #667eea;
}

.module-info-display p {
    margin: 0 0 10px 0;
    color: #666;
}

.example-prompt {
    font-size: 14px;
    color: #888;
    font-style: italic;
}

textarea {
    width: 100%;
    padding: 15px;
    border: 2px solid #ddd;
    border-radius: 8px;
    font-size: 16px;
    resize: vertical;
    min-height: 100px;
}

textarea:focus {
    outline: none;
    border-color: #667eea;
}

.form-controls {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.quantum-submit-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 12px 25px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    transition: transform 0.2s ease;
}

.quantum-submit-btn:hover:not(:disabled) {
    transform: translateY(-2px);
}

.quantum-submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.example-btn {
    background: #f8f9fa;
    color: #495057;
    border: 2px solid #dee2e6;
    padding: 12px 20px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
}

.example-btn:hover {
    background: #e9ecef;
}

.quantum-results {
    background: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
}

.quantum-results h3 {
    margin-top: 0;
    color: #333;
}

.result-container {
    margin-top: 15px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 10px;
    border-left: 4px solid #667eea;
}

.result-content {
    white-space: pre-wrap;
    line-height: 1.6;
    color: #333;
    margin-bottom: 15px;
}

.result-actions {
    display: flex;
    gap: 10px;
}

.result-actions button {
    background: #6c757d;
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 12px;
}

.result-actions button:hover {
    background: #5a6268;
}

.empty-state, .loading-state {
    text-align: center;
    padding: 40px 20px;
    color: #666;
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.quantum-metrics {
    background: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    margin-top: 20px;
}

.quantum-metrics h4 {
    margin-top: 0;
    color: #333;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
}

.metric {
    text-align: center;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 8px;
}

.metric-label {
    display: block;
    font-size: 12px;
    color: #666;
    margin-bottom: 5px;
}

.metric-value {
    display: block;
    font-size: 18px;
    font-weight: bold;
    color: #667eea;
}

@media (max-width: 768px) {
    .quantum-playground {
        padding: 10px;
    }

    .module-grid {
        grid-template-columns: 1fr;
    }

    .form-controls {
        flex-direction: column;
    }
}
`;

// Export for use in other components
export { QuantumPlayground, quantumStyles };
export default QuantumPlayground;