import { useEffect, useState } from "react";
import { listFlows, startFlow } from "../services/flows";
import WorkflowDetail from "./WorkflowDetail";

// Simple Workflow Dashboard (MVP)
// - Lists existing workflows
// - Start new workflow with goal + tool selection
// - Shows detail panel with live events
export default function WorkflowDashboard() {
  const [flows, setFlows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [goal, setGoal] = useState("");
  const [tool, setTool] = useState("echo");
  const [selected, setSelected] = useState(null);

  async function refresh() {
    try {
      setLoading(true);
      const data = await listFlows();
      setFlows(data.workflows || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, []);

  async function handleStart(e) {
    e.preventDefault();
    setError(null);
    if (!goal.trim()) return;
    try {
      const res = await startFlow({ goal, tools: [tool] });
      setGoal("");
      setSelected(res.workflow_id);
      refresh();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 text-gray-200">
      <h2 className="text-2xl font-bold mb-3">Workflow Dashboard</h2>

      {/* Start new workflow */}
      <form onSubmit={handleStart} className="flex gap-2 mb-4">
        <input
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Goal (e.g., generate product description)"
          className="flex-1 bg-black/40 border border-gray-700 rounded px-3 py-2 focus:outline-none"
        />
        <select
          value={tool}
          onChange={(e) => setTool(e.target.value)}
          className="bg-black/40 border border-gray-700 rounded px-2"
        >
          <option value="echo">Echo</option>
          <option value="gemini_text">Gemini (Vertex AI)</option>
        </select>
        <button
          type="submit"
          className="bg-neonBlue hover:bg-blue-500 text-black font-semibold px-4 py-2 rounded"
        >Start</button>
      </form>
      {error && <p className="text-red-400 text-sm mb-2">{error}</p>}

      {/* List workflows */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {loading && <p>Loading...</p>}
        {flows.map((wf) => (
          <div key={wf.workflow_id} className="bg-black/30 border border-gray-800 rounded p-3">
            <div className="flex justify-between items-center">
              <div>
                <div className="text-sm text-gray-400">{wf.workflow_id}</div>
                <div className="font-semibold">{wf.goal}</div>
                <div className="text-xs text-gray-500">Status: {wf.status}</div>
              </div>
              <button
                className="text-neonOrange hover:underline"
                onClick={() => setSelected(wf.workflow_id)}
              >Open</button>
            </div>
          </div>
        ))}
        {flows.length === 0 && !loading && (
          <p className="text-gray-400">No workflows yet. Start one above.</p>
        )}
      </div>

      {/* Detail view */}
      {selected && (
        <div className="mt-4">
          <WorkflowDetail workflowId={selected} onClose={() => setSelected(null)} />
        </div>
      )}
    </div>
  );
}