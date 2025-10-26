import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const AI_PROVIDERS = [
    { id: 'auto', name: '🤖 OMNI Director', desc: 'Inteligentno izbere najboljšo AI' },
    { id: 'openai', name: '💬 ChatGPT', desc: 'Odličen za ustvarjanje in kodiranje' },
    { id: 'gemini', name: '🔍 Gemini', desc: 'Odličen za analize in raziskave' },
    { id: 'omni', name: '🏠 OMNI AI', desc: 'Lokalne OMNI funkcije' }
];

export default function OmniChat({ isOpen, onClose }) {
    const [messages, setMessages] = useState([
        {
            id: 1,
            type: 'bot',
            content: '👋 Pozdravljeni! Sem OMNI Director, vaš slovenski AI asistent.\n\n💡 Trenutno delujem v STANDALONE načinu - vsi odgovori prihajajo iz OMNI AI sistema.\n\nČe želite uporabljati ChatGPT ali Gemini, nastavite API ključe v environment variables:\n• OPENAI_API_KEY=sk-your-key\n• GEMINI_API_KEY=your-key\n\nKako vam lahko pomagam?',
            timestamp: new Date()
        }
    ]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [selectedAI, setSelectedAI] = useState('omni');
    const [connectionStatus, setConnectionStatus] = useState('checking');
    const messagesEndRef = useRef(null);

    // Preveri povezavo z API-jem
    useEffect(() => {
        checkConnection();
    }, []);

    // Auto-scroll to bottom when new messages
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const checkConnection = async () => {
        try {
            const response = await axios.get('http://localhost:3001/api/health');
            setConnectionStatus('connected');
        } catch (error) {
            console.error('API connection failed:', error);
            setConnectionStatus('error');
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const sendMessage = async () => {
        if (!inputMessage.trim() || isLoading) return;

        const userMessage = {
            id: messages.length + 1,
            type: 'user',
            content: inputMessage,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsLoading(true);

        try {
            console.log(`📤 Sending to ${selectedAI}:`, inputMessage);

            const response = await axios.post('http://localhost:3001/api/chat', {
                message: inputMessage,
                userId: 'web-user',
                aiProvider: selectedAI
            });

            if (response.data.success) {
                const botMessage = {
                    id: messages.length + 2,
                    type: 'bot',
                    content: response.data.response,
                    timestamp: new Date(),
                    aiProvider: response.data.usedAI,
                    conversationId: response.data.conversationId
                };

                setMessages(prev => [...prev, botMessage]);
                console.log(`✅ Response from ${response.data.usedAI}`);
            } else {
                throw new Error(response.data.error || 'Unknown error');
            }

        } catch (error) {
            console.error('❌ Chat error:', error);

            let errorContent = `❌ Oprostite, prišlo je do napake: ${error.message}`;

            if (error.message.includes('API key')) {
                errorContent += '\n\n💡 Rešitev: Preverite OPENAI_API_KEY v environment variables.';
            } else if (error.message.includes('Invalid character')) {
                errorContent += '\n\n💡 Rešitev: API ključ vsebuje neveljavne znake. Preverite format ključa.';
            } else if (error.message.includes('timeout')) {
                errorContent += '\n\n💡 Rešitev: AI storitev ne odgovarja. Poskusite z OMNI AI ali pozneje.';
            } else {
                errorContent += '\n\n💡 Rešitev: Poskusite z OMNI AI providerjem ali preverite internetno povezavo.';
            }

            const errorMessage = {
                id: messages.length + 2,
                type: 'bot',
                content: errorContent,
                timestamp: new Date(),
                isError: true
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const clearChat = () => {
        setMessages([messages[0]]); // Keep only the welcome message
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    className="bg-gray-900 rounded-2xl w-full max-w-4xl h-[80vh] flex flex-col border border-neonBlue/30"
                    onClick={e => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-gray-700">
                        <div className="flex items-center space-x-3">
                            <div className="text-2xl">🤖</div>
                            <div>
                                <h2 className="text-xl font-bold text-neonBlue">OMNI Chat</h2>
                                <p className="text-sm text-gray-400">
                                    🔵 {connectionStatus === 'connected' ? 'Povezan' : 'Ni povezave'} |
                                    Selected AI: {AI_PROVIDERS.find(p => p.id === selectedAI)?.name}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-2">
                            <select
                                value={selectedAI}
                                onChange={(e) => setSelectedAI(e.target.value)}
                                className="bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 focus:border-neonBlue focus:outline-none"
                            >
                                {AI_PROVIDERS.map(provider => (
                                    <option key={provider.id} value={provider.id}>
                                        {provider.name}
                                    </option>
                                ))}
                            </select>
                            <button
                                onClick={clearChat}
                                className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                            >
                                🗑️
                            </button>
                            <button
                                onClick={onClose}
                                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                            >
                                ✕
                            </button>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-4">
                        {messages.map((message) => (
                            <motion.div
                                key={message.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div className={`max-w-[70%] p-4 rounded-2xl ${
                                    message.type === 'user'
                                        ? 'bg-neonBlue text-black'
                                        : message.isError
                                        ? 'bg-red-900/50 text-red-200 border border-red-500/30'
                                        : 'bg-gray-800 text-gray-100 border border-gray-700'
                                }`}>
                                    <div className="whitespace-pre-wrap">{message.content}</div>
                                    {message.aiProvider && (
                                        <div className="text-xs mt-2 opacity-60 font-mono">
                                            🤖 {message.aiProvider.toUpperCase()}
                                        </div>
                                    )}
                                    <div className="text-xs mt-1 opacity-50">
                                        {message.timestamp.toLocaleTimeString()}
                                    </div>
                                </div>
                            </motion.div>
                        ))}

                        {isLoading && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="flex justify-start"
                            >
                                <div className="bg-gray-800 p-4 rounded-2xl border border-gray-700">
                                    <div className="flex items-center space-x-2">
                                        <div className="flex space-x-1">
                                            <div className="w-2 h-2 bg-neonBlue rounded-full animate-bounce"></div>
                                            <div className="w-2 h-2 bg-neonPink rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                                            <div className="w-2 h-2 bg-neonOrange rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                                        </div>
                                        <span className="text-sm text-gray-400">Razmišljam...</span>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input */}
                    <div className="p-6 border-t border-gray-700">
                        <div className="flex space-x-3">
                            <textarea
                                value={inputMessage}
                                onChange={(e) => setInputMessage(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="Vpišite sporočilo... (Enter za pošiljanje, Shift+Enter za novo vrstico)"
                                className="flex-1 bg-gray-800 text-white p-4 rounded-xl border border-gray-600 focus:border-neonBlue focus:outline-none resize-none"
                                rows={3}
                                disabled={isLoading}
                            />
                            <button
                                onClick={sendMessage}
                                disabled={!inputMessage.trim() || isLoading}
                                className="px-6 py-3 bg-gradient-to-r from-neonBlue to-neonPink text-black font-bold rounded-xl hover:shadow-lg hover:shadow-neonBlue/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                📤
                            </button>
                        </div>
                        <div className="mt-3 text-xs text-gray-400 text-center">
                            💡 Nasveti: Vprašajte karkoli v slovenščini • Uporabite različna AI za različne naloge • Sistem deluje 24/7
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}