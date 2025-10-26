from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="", tags=["admin-ui"])

@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    html = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Admin Dashboard</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; padding: 20px; background: #f7f7fb; }
    h1 { margin-top: 0; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .card { background: white; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    .toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
    input, button { padding: 8px 10px; border-radius: 6px; border: 1px solid #d0d0da; }
    button { background: #2b6ef5; color: white; border: none; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px; border-bottom: 1px solid #eee; text-align: left; }
    .small { font-size: 12px; color: #666; }
    .row { display: flex; gap: 8px; align-items: center; }
    .danger { background: #e53e3e; }
  </style>
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
</head>
<body>
  <h1>Admin Dashboard</h1>
  <div class=\"toolbar\">
    <div class=\"row\">
      <label>Tenant ID</label>
      <input id=\"tenantId\" placeholder=\"demo-tenant\" value=\"demo-tenant\" />
    </div>
    <div class=\"row\">
      <label>API key</label>
      <input id=\"apiKey\" placeholder=\"(auto)\" />
    </div>
    <button id=\"btnAuth\">Get Token</button>
    <span id=\"authStatus\" class=\"small\"></span>
  </div>

  <div class=\"toolbar\">
    <button id=\"btnGenerate\">Generate from Market Data</button>
    <button id=\"btnAddItem\">Add Catalog Item</button>
  </div>

  <div class=\"grid\">
    <div class=\"card\">
      <h3>Revenue History</h3>
      <canvas id=\"revChart\" height=\"180\"></canvas>
      <div id=\"revList\"></div>
    </div>

    <div class=\"card\">
      <h3>Billing Catalog</h3>
      <table>
        <thead>
          <tr><th>Name</th><th>Price</th><th>Currency</th><th>Actions</th></tr>
        </thead>
        <tbody id=\"catalogBody\"></tbody>
      </table>
    </div>
  </div>

<script>
const apiBase = window.location.origin + '/api/v1';
let apiKey = '';
let tenantId = 'demo-tenant';

function headers(){
  return { 'Content-Type':'application/json', 'x-api-key': apiKey, 'tenant_id': tenantId };
}

async function getToken(){
  tenantId = document.getElementById('tenantId').value || 'demo-tenant';
  const r = await fetch(`${apiBase}/auth/tenant`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ tenant_id: tenantId })});
  const j = await r.json();
  apiKey = (j.tenant && j.tenant.api_key) || '';
  document.getElementById('apiKey').value = apiKey;
  document.getElementById('authStatus').textContent = apiKey ? 'OK' : 'Failed';
}

async function loadRevenue(){
  const r = await fetch(`${apiBase}/policy/revenue/history`, { headers: headers()});
  const j = await r.json();
  const items = (j.history || []);
  // render list
  const listEl = document.getElementById('revList');
  listEl.innerHTML = items.map(it => `<div class=\"small\">${new Date(it.created_at).toLocaleString()} • ${it.feature_name} • rollout=${it.rollout}% • ${it.notes||''}</div>`).join('');
  // chart
  const ctx = document.getElementById('revChart');
  const labels = items.map(it => new Date(it.created_at).toLocaleTimeString());
  const data = items.map(it => it.rollout || 0);
  if(window.revChartObj){ window.revChartObj.destroy(); }
  window.revChartObj = new Chart(ctx, { type:'bar', data:{ labels, datasets:[{ label:'Rollout %', data, backgroundColor:'#2b6ef5'}] }, options:{ responsive:true, maintainAspectRatio:false }});
}

async function loadCatalog(){
  const r = await fetch(`${apiBase}/billing/catalog`, { headers: headers()});
  const j = await r.json();
  const tbody = document.getElementById('catalogBody');
  tbody.innerHTML = (j.items||[]).map(it => `
    <tr>
      <td>${it.name}</td>
      <td>${it.price_per_call}</td>
      <td>${it.currency}</td>
      <td>
        <button onclick=\"updateItem('${it.id}')\">PUT</button>
        <button class=\"danger\" onclick=\"deleteItem('${it.id}')\">DELETE</button>
      </td>
    </tr>
  `).join('');
}

async function updateItem(id){
  const r = await fetch(`${apiBase}/billing/catalog/${id}`, { method:'PUT', headers: headers(), body: JSON.stringify({ description: 'Updated via Admin UI' })});
  await r.json();
  await loadCatalog();
}

async function deleteItem(id){
  const r = await fetch(`${apiBase}/billing/catalog/${id}`, { method:'DELETE', headers: headers()});
  await r.json();
  await loadCatalog();
}

async function generateFromMarket(){
  const payload = { trends: [ { name:'AI-Translate', price:0.03, currency:'USD' }, { name:'Image-Upscale', price:0.05, currency:'USD' } ] };
  const r = await fetch(`${apiBase}/rl/market/process`, { method:'POST', headers: headers(), body: JSON.stringify(payload)});
  await r.json();
  await loadCatalog();
  await loadRevenue();
}

async function addCatalogItem(){
  const payload = { name:'TempItem', price_per_call:0.02, currency:'USD', path:'/api/v1/temp', tenant_id: tenantId, description:'Temporary test item' };
  const r = await fetch(`${apiBase}/billing/catalog/add`, { method:'POST', headers: headers(), body: JSON.stringify(payload)});
  await r.json();
  await loadCatalog();
}

// init
window.addEventListener('DOMContentLoaded', async () => {
  document.getElementById('btnAuth').addEventListener('click', getToken);
  document.getElementById('btnGenerate').addEventListener('click', generateFromMarket);
  document.getElementById('btnAddItem').addEventListener('click', addCatalogItem);
  await getToken();
  await loadRevenue();
  await loadCatalog();
});
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)
