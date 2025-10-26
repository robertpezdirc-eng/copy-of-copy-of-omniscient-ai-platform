import { useEffect, useState } from "react";
import { getFlow, getFlowEvents, streamFlowEvents, executeStep } from "../services/flows";

// Detail view with real-time updates via SSE
export default function WorkflowDetail({ workflowId, onClose }) {
  const [flow, setFlow] = useState(null);
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    let es;
    async function init() {
      try {
        const data = await getFlow(workflowId);
        setFlow(data);
        const ev = await getFlowEvents(workflowId);
        setEvents(ev.events || []);
        es = streamFlowEvents(workflowId);
        es.onmessage = (msg) => {
          try {
            const json = JSON.parse(msg.data);
            setEvents((prev) => [...prev, json]);
          } catch (e) {}
        };
        es.onerror = (e) => {
          console.warn("SSE error", e);
        };
      } catch (e) {
        setError(e.message);
      }
    }
    init();
    return () => {
      if (es) es.close();
    };
  }, [workflowId]);

  async function runFirstStepLocally() {
    try {
      setRunning(true);
      const step = flow?.plan?.steps?.[0];
      if (!step) return;
      await executeStep(workflowId, step);
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="bg-black/40 border border-gray-800 rounded p-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-xl font-bold">Workflow: {workflowId}</h3>
        <button className="text-neonPink hover:underline" onClick={onClose}>Close</button>
      </div>
      {error && <p className="text-red-400 text-sm mb-2">{error}</p>}
      {flow ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Plan */}
          <div className="bg-gray-900/50 border border-gray-800 rounded p-3">
            <h4 className="font-semibold mb-2">Plan</h4>
            <div className="text-sm text-gray-300">Goal: {flow.goal}</div>
            <ul className="mt-2 text-sm">
              {(flow.plan?.steps || []).map((s) => (
                <li key={s.id} className="mb-1">
                  <span className="font-mono text-xs text-gray-400">{s.id}</span>{" "}
                  <span className="font-semibold">{s.tool}</span>{" "}
                  <span className="text-gray-400">inputs: {Object.keys(s.inputs || {}).join(", ")}</span>
                </li>
              ))}
            </ul>
            <button
              className="mt-2 bg-neonOrange text-black px-3 py-1 rounded disabled:opacity-50"
              disabled={running}
              onClick={runFirstStepLocally}
            >Run first step locally</button>
          </div>

          {/* Live Events */}
          <div className="bg-gray-900/50 border border-gray-800 rounded p-3">
            <h4 className="font-semibold mb-2">Live Events</h4>
            <div className="max-h-48 overflow-auto text-sm">
              {events.map((e, i) => (
                <div key={i} className="border-b border-gray-800 py-1">
                  <span className="font-mono text-xs text-gray-500 mr-2">{e.ts || ""}</span>
                  <span className="text-neonBlue mr-2">{e.event}</span>
                  <span className="text-gray-300">{JSON.stringify(e.detail)}</span>
                </div>
              ))}
              {events.length === 0 && (
                <div className="text-gray-400">No events yet.</div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}