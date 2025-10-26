import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import OmniChat from "./OmniChat";
import WorkflowDashboard from "./components/WorkflowDashboard";

const omniAgents = [
  {
    name: "Omni Director",
    desc: "Glavni direktor AI sistemov, nadzira agente.",
    type: "director",
    status: "active",
    api: "http://localhost:3001/api/agents/ceo-001"
  },
  {
    name: "Data Analyzer",
    desc: "Analizira podatke v realnem času in ustvarja poročila.",
    type: "analyzer",
    status: "active",
    api: "http://localhost:3001/api/agents/data-analyzer"
  },
  {
    name: "Omni Chat",
    desc: "AI asistent za uporabnike, podobno kot ChatGPT.",
    type: "assistant",
    status: "active",
    api: "http://localhost:3001/api/chat"
  },
  {
    name: "Vision Core",
    desc: "Obdelava slik in zaznavanje objektov.",
    type: "vision",
    status: "active",
    api: "http://localhost:3001/api/vision"
  },
  {
    name: "Omni Billing",
    desc: "Sistem za upravljanje naročnin in plačil.",
    type: "billing",
    status: "active",
    api: "http://localhost:3001/api/billing"
  },
  {
    name: "AI Generator",
    desc: "Ustvarja besedila, slike in kodo po naročilu.",
    type: "generator",
    status: "active",
    api: "http://localhost:3001/api/generator"
  },
  {
    name: "Security Sentinel",
    desc: "Nadzira dostop in varnostne protokole.",
    type: "security",
    status: "active",
    api: "http://localhost:3001/api/security"
  },
  {
    name: "Kilo Code",
    desc: "Generator programske kode in API integracij.",
    type: "developer",
    status: "active",
    api: "http://localhost:3001/api/code-generator"
  },
];

export default function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [systemStatus, setSystemStatus] = useState("initializing");
  const [connectedAgents, setConnectedAgents] = useState(0);
  const [apiHealth, setApiHealth] = useState("checking");
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [learningData, setLearningData] = useState(null);
  const [isWorkflowOpen, setIsWorkflowOpen] = useState(false);

  // Initialize system connection
  useEffect(() => {
    initializeOmniSystem();
  }, []);

  const initializeOmniSystem = async () => {
    try {
      // Check API connectivity with multiple attempts
      console.log("🔌 Checking API connectivity...");

      const response = await fetch('http://localhost:3001/api/health', {
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });

      if (response.ok) {
        const data = await response.json();
        console.log("✅ API Connected:", data);
        setApiHealth("connected");
        setSystemStatus("ready");
        setConnectedAgents(omniAgents.length);

        // Fetch learning data
        await fetchLearningData();
      } else {
        console.log("⚠️ API responded but not OK:", response.status);
        setApiHealth("standalone");
        setSystemStatus("ready");
        setConnectedAgents(omniAgents.length);
      }
    } catch (error) {
      console.log("🔌 Backend API not available, running in standalone mode");
      console.log("Error:", error.message);
      setApiHealth("standalone");
      setSystemStatus("ready");
      setConnectedAgents(omniAgents.length);
    }
  };

  const fetchLearningData = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/learning/status');
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setLearningData(data.learning_overlay);
          console.log("📚 Learning data loaded:", data.learning_overlay);
        }
      }
    } catch (error) {
      console.log("📚 Learning overlay not available:", error.message);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    console.log("🔍 Search triggered for:", query);

    if (!query.trim()) {
      setResults([]);
      return;
    }

    const filtered = omniAgents.filter(agent => {
      const searchTerm = query.toLowerCase();
      const matches = (
        agent.name.toLowerCase().includes(searchTerm) ||
        agent.desc.toLowerCase().includes(searchTerm) ||
        agent.type.toLowerCase().includes(searchTerm)
      );
      if (matches) {
        console.log(`✅ Match found: ${agent.name} (${agent.type})`);
      }
      return matches;
    });

    // Special case: show all agents for "omni" search
    if (query.toLowerCase().includes("omni") && filtered.length === 0) {
      console.log("🌟 Showing all agents for 'omni' search");
      return omniAgents;
    }

    return filtered;

    console.log(`📊 Total results: ${filtered.length}`);
    setResults(filtered);
  };

  const connectToAgent = async (agent) => {
    try {
      const response = await fetch(`${agent.api}/status`);
      if (response.ok) {
        const data = await response.json();
        console.log(`Connected to ${agent.name}:`, data);
        setSystemStatus(`connected-${agent.type}`);
      }
    } catch (error) {
      console.error(`Failed to connect to ${agent.name}:`, error);
    }
  };

  const getStatusColor = () => {
    switch (systemStatus) {
      case "ready": return "text-neonBlue";
      case "connected-director": return "text-neonPink";
      case "connected-assistant": return "text-neonOrange";
      case "error": return "text-red-500";
      case "offline": return "text-gray-500";
      default: return "text-neonBlue";
    }
  };

  const getStatusIcon = () => {
    switch (apiHealth) {
      case "connected": return "🟢";
      case "standalone": return "🔵";
      case "error": return "🔴";
      case "disconnected": return "⚫";
      default: return "🔵";
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-gray-900 via-black to-gray-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-neonBlue opacity-10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-neonPink opacity-10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-neonOrange opacity-10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Matrix-style background pattern */}
      <div className="absolute inset-0 opacity-5">
        {Array.from({ length: 20 }).map((_, i) => (
          <div key={i} className="absolute font-mono text-xs text-neonBlue animate-pulse"
               style={{
                 left: `${Math.random() * 100}%`,
                 top: `${Math.random() * 100}%`,
                 animationDelay: `${Math.random() * 3}s`
               }}>
            {Math.random().toString(36).substring(7)}
          </div>
        ))}
      </div>

      <div className="relative z-10 w-full max-w-4xl px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-7xl font-black mb-4 tracking-wider">
            <span className="text-neonBlue neon-glow">O</span>
            <span className="text-neonPink neon-glow mx-2">M</span>
            <span className="text-neonOrange neon-glow">N</span>
            <span className="text-neonBlue neon-glow ml-2">I</span>
          </h1>
          <p className="text-xl text-gray-300 font-mono">
            {getStatusIcon()} System Status: <span className={getStatusColor()}>
              {systemStatus === "ready" && apiHealth === "standalone" ? "STANDALONE" :
               systemStatus === "ready" && apiHealth === "connected" ? "READY" :
               systemStatus === "initializing" ? "INITIALIZING" :
               systemStatus.startsWith("connected-") ? "AGENT CONNECTED" :
               systemStatus.toUpperCase()}
            </span>
          </p>
          <p className="text-sm text-gray-400 mt-2">
            Connected Agents: {connectedAgents} | API Health: {apiHealth}
          </p>
        </motion.div>

        {/* Search Form */}
        <motion.form
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          onSubmit={handleSearch}
          className="text-center mb-8"
        >
          <div className="relative max-w-2xl mx-auto">
            <input
              type="text"
              value={query}
              onChange={(e) => {
                const value = e.target.value;
                setQuery(value);
                console.log("🔍 Real-time search for:", value);

                // Real-time search as you type
                if (value.trim()) {
                  const filtered = omniAgents.filter(agent => {
                    const searchTerm = value.toLowerCase();
                    return (
                      agent.name.toLowerCase().includes(searchTerm) ||
                      agent.desc.toLowerCase().includes(searchTerm) ||
                      agent.type.toLowerCase().includes(searchTerm)
                    );
                  });
                  console.log(`✅ Real-time results: ${filtered.length}`, filtered);
                  setResults(filtered);
                } else {
                  setResults([]);
                }
              }}
              placeholder="Search OMNI agents, APIs, or modules..."
              className="w-full px-8 py-6 text-xl rounded-full bg-black/50 backdrop-blur-sm border-2 border-neonBlue/30 text-white placeholder-gray-400 focus:outline-none focus:border-neonPink focus:ring-2 focus:ring-neonPink/20 transition-all duration-300"
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 transform -translate-y-1/2 px-6 py-3 bg-gradient-to-r from-neonBlue to-neonPink text-black font-bold rounded-full hover:shadow-lg hover:shadow-neonBlue/50 transition-all duration-300 transform hover:scale-105"
            >
              Search
            </button>
          </div>
        </motion.form>

        {/* Search Results */}
        <AnimatePresence>
          {results.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              {results.map((agent, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="bg-black/40 backdrop-blur-sm border border-gray-700 rounded-xl p-6 hover:border-neonBlue/50 hover:bg-black/60 transition-all duration-300 cursor-pointer group"
                  onClick={() => connectToAgent(agent)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="text-2xl font-bold text-neonPink group-hover:text-neonBlue transition-colors">
                        {agent.name}
                      </h3>
                      <p className="text-gray-300 mt-2">{agent.desc}</p>
                      <div className="flex items-center mt-3 space-x-4">
                        <span className="px-3 py-1 bg-neonBlue/20 text-neonBlue rounded-full text-sm font-mono">
                          {agent.type}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-sm font-mono ${
                          agent.status === 'active'
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-gray-500/20 text-gray-400'
                        }`}>
                          {agent.status}
                        </span>
                      </div>
                    </div>
                    <div className="text-4xl group-hover:scale-110 transition-transform">
                      {agent.type === 'director' && '👑'}
                      {agent.type === 'analyzer' && '📊'}
                      {agent.type === 'assistant' && '🤖'}
                      {agent.type === 'vision' && '👁️'}
                      {agent.type === 'billing' && '💳'}
                      {agent.type === 'generator' && '⚡'}
                      {agent.type === 'security' && '🛡️'}
                      {agent.type === 'developer' && '💻'}
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* No results state */}
        {query && results.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-2xl font-bold text-gray-400 mb-2">No agents found</h3>
            <p className="text-gray-500">Try searching for: Director, Chat, Vision, Security...</p>
            <div className="mt-4 text-sm text-gray-400">
              <p>💡 Search tips:</p>
              <p>• Type "omni" to see all agents</p>
              <p>• Search by type: "assistant", "security", "vision"</p>
              <p>• Search by name: "Director", "Chat", "Kilo Code"</p>
            </div>
          </motion.div>
        )}

        {/* Learning Data Display */}
        {learningData && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-6 bg-black/20 backdrop-blur-sm border border-neonBlue/30 rounded-xl"
          >
            <h3 className="text-xl font-bold text-neonBlue mb-4 flex items-center">
              📚 OMNI Learning Overlay
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-neonPink">{learningData.total_agents_learning}</div>
                <div className="text-sm text-gray-400">Učeči se agenti</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-neonOrange">{learningData.total_topics_learned}</div>
                <div className="text-sm text-gray-400">Naučenih tem</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-neonBlue">{Object.keys(learningData.agents_memory || {}).length}</div>
                <div className="text-sm text-gray-400">Aktivni agenti</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">🟢</div>
                <div className="text-sm text-gray-400">Status: Aktiven</div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Show sample agents when no query */}
        {!query && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-8"
          >
            <h3 className="text-xl font-bold text-neonBlue mb-4">🤖 Available OMNI Agents</h3>
            <p className="text-gray-400 mb-4">Start typing to search agents...</p>
            <div className="text-sm text-gray-500">
              <p>💡 Quick searches: "omni", "director", "chat", "security"</p>
            </div>
          </motion.div>
        )}

        {/* Toggle Workflow Dashboard */}
        <motion.button
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="fixed bottom-6 left-6 w-16 h-16 bg-gradient-to-r from-neonOrange to-neonPink rounded-full shadow-lg hover:shadow-neonOrange/50 transition-all duration-300 flex items-center justify-center text-2xl font-bold hover:scale-110 z-40"
          onClick={() => setIsWorkflowOpen((v) => !v)}
          title="Odpri Workflow Dashboard"
        >
          ⚙️
        </motion.button>

        {isWorkflowOpen && (
          <div className="fixed bottom-24 left-6 right-6 z-30">
            <WorkflowDashboard />
          </div>
        )}

        {/* Chat Button */}
        <motion.button
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-r from-neonBlue to-neonPink rounded-full shadow-lg hover:shadow-neonBlue/50 transition-all duration-300 flex items-center justify-center text-2xl font-bold hover:scale-110 z-40"
          onClick={() => setIsChatOpen(true)}
          title="Odpri OMNI Chat"
        >
          💬
        </motion.button>

        {/* Chat Component */}
        <OmniChat isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="text-center mt-16 text-gray-500 font-mono text-sm"
        >
          <p>OMNI Search Engine v2.1 | Connected to {connectedAgents} agents</p>
          <p className="mt-2">
            <span className="text-neonBlue">API:</span> {apiHealth === "standalone" ? "Standalone" : apiHealth} |
            <span className="text-neonPink ml-2">WebSocket:</span> Active |
            <span className="text-neonOrange ml-2">Modules:</span> Loaded
          </p>
        </motion.div>
      </div>
    </div>
  );
}