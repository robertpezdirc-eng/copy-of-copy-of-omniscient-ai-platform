from typing import Any, Dict, Optional
from fastapi import APIRouter, Header, HTTPException
import os
import json
import uuid

router = APIRouter(prefix="/auth", tags=["auth"]) 

STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
KEYS_FILE = os.path.join(STORE_DIR, "access_keys.json")
AGENTS_FILE = os.path.join(STORE_DIR, "user_agents.json")


def _ensure():
    os.makedirs(STORE_DIR, exist_ok=True)
    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    if not os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _load() -> Dict[str, Any]:
    _ensure()
    try:
        return json.load(open(KEYS_FILE, "r", encoding="utf-8"))
    except Exception:
        return {}

# New unified UserAgent store helpers

def _load_agents() -> Dict[str, Any]:
    _ensure()
    try:
        return json.load(open(AGENTS_FILE, "r", encoding="utf-8"))
    except Exception:
        return {}


def _save_agents(data: Dict[str, Any]):
    _ensure()
    json.dump(data, open(AGENTS_FILE, "w", encoding="utf-8"), indent=2)


@router.post('/tenant')
def create_tenant(payload: Dict[str, Any]) -> Dict[str, Any]:
    agents = _load_agents()
    tenant_id = payload.get('tenant_id') or uuid.uuid4().hex[:8]
    api_key = uuid.uuid4().hex
    agents[tenant_id] = {
        'tenant_id': tenant_id,
        'api_key': api_key,
        'roles': payload.get('roles') or ['user'],
        'real_name': payload.get('real_name') or '',
        'billing_address': payload.get('billing_address') or '',
        'contact_email': payload.get('contact_email') or '',
        'compliance_status': payload.get('compliance_status') or 'unknown',
        'created_at': uuid.uuid1().time,
    }
    _save_agents(agents)
    return {'ok': True, 'tenant': agents[tenant_id]}


@router.get('/token/{tenant_id}')
def get_token(tenant_id: str) -> Dict[str, Any]:
    agents = _load_agents()
    if tenant_id not in agents:
        raise HTTPException(status_code=404, detail='tenant not found')
    return {'tenant_id': tenant_id, 'api_key': agents[tenant_id]['api_key']}


@router.post('/apikey/rotate')
def rotate_key(payload: Dict[str, Any]) -> Dict[str, Any]:
    tenant_id = payload.get('tenant_id')
    if not tenant_id:
        raise HTTPException(status_code=400, detail='tenant_id required')
    agents = _load_agents()
    if tenant_id not in agents:
        raise HTTPException(status_code=404, detail='tenant not found')
    agents[tenant_id]['api_key'] = uuid.uuid4().hex
    _save_agents(agents)
    return {'ok': True, 'api_key': agents[tenant_id]['api_key']}


@router.post('/verify')
def verify(x_api_key: Optional[str] = Header(default=None), tenant: Optional[str] = Header(default=None, alias="tenant_id")) -> Dict[str, Any]:
    agents = _load_agents()
    for tid, rec in agents.items():
        if rec.get('api_key') == x_api_key and (tenant is None or tenant == tid):
            return {'ok': True, 'tenant_id': tid, 'roles': rec.get('roles'), 'agent': rec}
    raise HTTPException(status_code=401, detail='invalid api key')


# Dependency helper so that other routers can import and enforce
async def require_api_key(x_api_key: Optional[str] = Header(default=None), tenant: Optional[str] = Header(default=None, alias="tenant_id")) -> Dict[str, Any]:
    agents = _load_agents()
    for tid, rec in agents.items():
        if rec.get('api_key') == x_api_key and (tenant is None or tenant == tid):
            return {'tenant_id': tid, 'roles': rec.get('roles'), 'agent': rec}
    raise HTTPException(status_code=401, detail='invalid api key')

# New endpoints to manage unified UserAgent profile

@router.get('/agent/{tenant_id}')
def get_agent(tenant_id: str) -> Dict[str, Any]:
    agents = _load_agents()
    if tenant_id not in agents:
        raise HTTPException(status_code=404, detail='tenant not found')
    return {'ok': True, 'agent': agents[tenant_id]}


@router.put('/agent')
def update_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
    tenant_id = payload.get('tenant_id')
    if not tenant_id:
        raise HTTPException(status_code=400, detail='tenant_id required')
    agents = _load_agents()
    if tenant_id not in agents:
        raise HTTPException(status_code=404, detail='tenant not found')
    # Allowed fields
    for key in ['real_name', 'billing_address', 'contact_email', 'compliance_status', 'roles']:
        if key in payload:
            agents[tenant_id][key] = payload[key]
    _save_agents(agents)
    return {'ok': True, 'agent': agents[tenant_id]}


@router.get('/tenants')
def list_tenants() -> Dict[str, Any]:
    keys = _load()
    tenants = []
    for tid, rec in keys.items():
        tenants.append({
            'tenant_id': tid,
            'api_key': rec.get('api_key'),
            'roles': rec.get('roles', []),
            'created_at': rec.get('created_at')
        })
    return {'ok': True, 'tenants': tenants}