import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const OmniRealChat = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    {
      from: 'omni',
      text: '👋 Pozdravljeni! Sem OMNI Director, vaš avtonomni AI asistent.\n\nTukaj sem da vam pomagam z realnimi informacijami o platformi v živo.',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message to chat
    const newMessage = {
      from: 'user',
      text: userMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, newMessage]);

    try {
      // Send request to OMNI Director API
      const response = await axios.post('http://localhost:8080/api/chat', {
        message: userMessage
      });

      // Add OMNI response to chat
      const omniResponse = {
        from: 'omni',
        text: response.data.reply,
        timestamp: new Date().toLocaleTimeString(),
        metadata: response.data.metadata
      };

      setMessages(prev => [...prev, omniResponse]);

    } catch (error) {
      console.error('Error sending message:', error);

      // Add error message to chat
      const errorMessage = {
        from: 'omni',
        text: `❌ Napaka pri povezavi z OMNI Director API.\n\nPreverite ali je API strežnik aktiven na http://localhost:8080\n\nNapaka: ${error.message}`,
        timestamp: new Date().toLocaleTimeString(),
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

  return (
    <div className="flex flex-col h-full w-full bg-darkBg text-white">
      {/* Header */}
      <div className="bg-darkGray p-4 border-b border-neonBlue/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-neonGreen rounded-full animate-pulse-slow"></div>
            <h1 className="text-xl font-bold text-neonBlue animate-glow">
              🌐 OMNI Director Chat
            </h1>
          </div>
          <div className="flex items-center space-x-2 text-sm text-lightGray">
            <div className="w-2 h-2 bg-neonBlue rounded-full"></div>
            <span>Real-Time</span>
          </div>
        </div>
        <p className="text-lightGray text-sm mt-1">
          Avtonomni AI asistent za real-time odgovore platforme
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.from === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                msg.from === 'user'
                  ? 'bg-neonBlue text-darkBg'
                  : msg.isError
                  ? 'bg-red-900/50 text-red-300 border border-red-500/50'
                  : 'bg-darkGray text-white border border-neonPink/30'
              }`}
            >
              <div className="whitespace-pre-wrap text-sm">
                {msg.text}
              </div>
              <div className={`text-xs mt-2 ${
                msg.from === 'user' ? 'text-darkBg/70' : 'text-lightGray'
              }`}>
                {msg.timestamp}
              </div>
              {msg.metadata && (
                <div className="text-xs text-neonGreen mt-1">
                  Query: {msg.metadata.query_type}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-darkGray text-white px-4 py-2 rounded-lg border border-neonPink/30">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-neonBlue rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-neonPink rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-neonGreen rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
                <span className="text-sm text-lightGray">OMNI Director razmišlja...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-darkGray border-t border-neonBlue/30">
        <div className="flex space-x-2">
          <input
            className="flex-1 p-3 rounded-lg bg-[#222] text-white border border-lightGray/50 focus:border-neonBlue focus:outline-none focus:ring-2 focus:ring-neonBlue/50 transition-all"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Pogovarjaj se z Omni direktorjem..."
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-neonPink text-darkBg font-bold rounded-lg hover:bg-neonPink/80 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? '...' : 'Pošlji'}
          </button>
          <button
            onClick={clearChat}
            className="px-4 py-3 bg-darkBg text-neonBlue border border-neonBlue/50 rounded-lg hover:bg-neonBlue/10 transition-all"
          >
            🗑️
          </button>
        </div>

        {/* Status Bar */}
        <div className="flex items-center justify-between mt-3 text-xs text-lightGray">
          <div className="flex items-center space-x-4">
            <span>💬 Real-Time Chat</span>
            <span>🤖 Autonomous Director</span>
            <span>⚡ Live Platform Data</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-neonGreen rounded-full animate-pulse-slow"></div>
            <span>API: http://localhost:8080</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OmniRealChat;