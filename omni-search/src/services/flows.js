// Workflow API + SSE client for OMNI orchestration
// Reads API base from environment with safe defaults.

const API_BASE =
  process.env.REACT_APP_OMNI_API_BASE ||
  process.env.OMNI_API_BASE ||
  "http://localhost:8080"; // FastAPI default dev port

export async function startFlow({ goal, tools = ["echo"], context = {}, constraints = {} }) {
  const res = await fetch(`${API_BASE}/api/flows/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal, tools, context, constraints }),
  });
  if (!res.ok) throw new Error(`Start flow failed: ${res.status}`);
  return res.json();
}

export async function listFlows() {
  const res = await fetch(`${API_BASE}/api/flows/`);
  if (!res.ok) throw new Error(`List flows failed: ${res.status}`);
  return res.json();
}

export async function getFlow(workflowId) {
  const res = await fetch(`${API_BASE}/api/flows/${workflowId}`);
  if (!res.ok) throw new Error(`Get flow failed: ${res.status}`);
  return res.json();
}

export async function getFlowEvents(workflowId) {
  const res = await fetch(`${API_BASE}/api/flows/${workflowId}/events`);
  if (!res.ok) throw new Error(`Get flow events failed: ${res.status}`);
  return res.json();
}

export function streamFlowEvents(workflowId) {
  // Return an EventSource instance to the caller for lifecycle management
  const url = `${API_BASE}/api/flows/${workflowId}/events/stream`;
  const es = new EventSource(url);
  return es;
}

export async function executeStep(workflowId, step) {
  const res = await fetch(`${API_BASE}/api/flows/${workflowId}/step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(step),
  });
  if (!res.ok) throw new Error(`Execute step failed: ${res.status}`);
  return res.json();
}