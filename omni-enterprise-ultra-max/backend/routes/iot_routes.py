"""from datetime import datetime, timezone

IoT Device Management & Telemetry Routesfrom typing import Optional, Dict, Any

"""

from fastapi import APIRouter, HTTPException, Body, Depends, Header

from fastapi import APIRouterfrom pydantic import BaseModel

from pydantic import BaseModelfrom jose import jwt, JWTError

from typing import List, Dict, Anyimport os

from datetime import datetime, timezoneimport asyncio

import uuid

import randomfrom utils.gcp import get_firestore



router = APIRouter()

router = APIRouter()



class DeviceRegistration(BaseModel):# Import WebSocket broadcaster (avoid circular import by importing function dynamically)

    device_name: str_ws_broadcaster = None

    device_type: str

    tenant_id: strJWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-prod")





@router.post("/devices/register")def get_current_user(authorization: Optional[str] = Header(None)):

async def register_device(device: DeviceRegistration):    if not authorization or not authorization.lower().startswith("bearer "):

    """Register new IoT device"""        raise HTTPException(status_code=401, detail="Missing token")

        token = authorization.split(" ", 1)[1]

    device_id = f"dev_{uuid.uuid4().hex[:12]}"    try:

            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

    return {        return payload

        "device_id": device_id,    except JWTError:

        "device_name": device.device_name,        raise HTTPException(status_code=401, detail="Invalid token")

        "device_type": device.device_type,

        "tenant_id": device.tenant_id,

        "status": "registered",class DeviceRegister(BaseModel):

        "api_key": f"iot_{uuid.uuid4().hex}",    device_id: str

        "registered_at": datetime.now(timezone.utc).isoformat()    name: Optional[str] = None

    }    model: Optional[str] = None





@router.get("/devices")@router.post("/devices/register")

async def list_devices(tenant_id: str):async def register_device(payload: DeviceRegister, user=Depends(get_current_user)):

    """List all devices for tenant"""    db = get_firestore()

        ref = db.collection("devices").document(payload.device_id)

    devices = [    data = {

        {        "device_id": payload.device_id,

            "device_id": f"dev_{i}",        "name": payload.name or payload.device_id,

            "device_name": f"Device {i}",        "model": payload.model,

            "status": random.choice(["online", "offline"]),        "tenant_id": user.get("tenant_id", "default"),

            "last_seen": datetime.now(timezone.utc).isoformat()        "created_at": datetime.now(timezone.utc).isoformat(),

        }        "owner": user.get("sub"),

        for i in range(1, 11)    }

    ]    ref.set(data)

        return data

    return {"tenant_id": tenant_id, "total": len(devices), "devices": devices}



class Telemetry(BaseModel):

@router.get("/devices/{device_id}/telemetry")    device_id: str

async def get_device_telemetry(device_id: str):    metrics: Dict[str, Any]

    """Get device telemetry data"""    ts: Optional[str] = None

    

    return {

        "device_id": device_id,@router.post("/telemetry/ingest")

        "telemetry": {async def ingest_telemetry(t: Telemetry, user=Depends(get_current_user)):

            "temperature": round(random.uniform(20, 30), 2),    db = get_firestore()

            "humidity": round(random.uniform(40, 60), 2),    # Ensure device exists and belongs to tenant

            "battery": random.randint(20, 100),    dref = db.collection("devices").document(t.device_id)

            "signal_strength": random.randint(-90, -30)    d = dref.get()

        },    if not d.exists:

        "timestamp": datetime.now(timezone.utc).isoformat()        raise HTTPException(status_code=404, detail="Device not registered")

    }    dten = d.to_dict().get("tenant_id")

    tenant_id = user.get("tenant_id")

    if dten != tenant_id:

@router.post("/devices/{device_id}/command")        raise HTTPException(status_code=403, detail="Device not in your tenant")

async def send_device_command(device_id: str, command: Dict[str, Any]):

    """Send command to device"""    ts = t.ts or datetime.now(timezone.utc).isoformat()

        ref = dref.collection("telemetry").document()

    return {    ref.set({"metrics": t.metrics, "ts": ts, "ingested_by": user.get("sub")})

        "device_id": device_id,    

        "command_id": f"cmd_{uuid.uuid4().hex[:10]}",    # Broadcast to WebSocket subscribers

        "status": "sent",    global _ws_broadcaster

        "sent_at": datetime.now(timezone.utc).isoformat()    if _ws_broadcaster is None:

    }        try:

            from routes.websocket_routes import notify_telemetry_subscribers
            _ws_broadcaster = notify_telemetry_subscribers
        except ImportError:
            pass
    
    if _ws_broadcaster:
        # Fire and forget - don't block ingestion
        asyncio.create_task(_ws_broadcaster(tenant_id, t.device_id, t.metrics))
    
    return {"status": "ok", "ts": ts}
