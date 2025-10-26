from typing import Any, Dict, Optional
from fastapi import APIRouter
import os
import json

router = APIRouter(prefix="/accel", tags=["accel"]) 

STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CONF_FILE = os.path.join(STORE_DIR, "accel_config.json")


def _ensure():
    os.makedirs(STORE_DIR, exist_ok=True)
    if not os.path.exists(CONF_FILE):
        with open(CONF_FILE, "w", encoding="utf-8") as f:
            json.dump({"gpu_preference": False, "memory": {"ramdisk_path": None, "swap_enabled": False}}, f)


def _load() -> Dict[str, Any]:
    _ensure()
    try:
        return json.load(open(CONF_FILE, "r", encoding="utf-8"))
    except Exception:
        return {"gpu_preference": False, "memory": {"ramdisk_path": None, "swap_enabled": False}}


def _save(data: Dict[str, Any]):
    _ensure()
    json.dump(data, open(CONF_FILE, "w", encoding="utf-8"), indent=2)


@router.get('/gpu/status')
def gpu_status() -> Dict[str, Any]:
    available = False
    details: Dict[str, Any] = {}
    try:
        import torch  # type: ignore
        available = bool(getattr(torch, 'cuda', None) and torch.cuda.is_available())
        if available:
            details['device_count'] = torch.cuda.device_count()
            details['current_device'] = torch.cuda.current_device()
            details['name'] = torch.cuda.get_device_name(details['current_device'])
    except Exception:
        available = False
    cfg = _load()
    return {'ok': True, 'gpu_available': available, 'gpu_preference': bool(cfg.get('gpu_preference')), 'details': details}


@router.post('/gpu/config')
def set_gpu_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load()
    cfg['gpu_preference'] = bool(payload.get('gpu_preference', cfg.get('gpu_preference', False)))
    _save(cfg)
    return {'ok': True, 'gpu_preference': cfg['gpu_preference']}


@router.post('/memory/config')
def memory_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load()
    mem = cfg.get('memory') or {}
    mem['ramdisk_path'] = payload.get('ramdisk_path', mem.get('ramdisk_path'))
    mem['swap_enabled'] = bool(payload.get('swap_enabled', mem.get('swap_enabled', False)))
    cfg['memory'] = mem
    _save(cfg)
    # Note: Creating a true RAM disk or OS swap changes requires system-level tooling,
    # which is outside the scope of this API. This endpoint stores preferences for agents
    # to honor when working with temporary files and large datasets.
    return {'ok': True, 'memory': cfg['memory']}