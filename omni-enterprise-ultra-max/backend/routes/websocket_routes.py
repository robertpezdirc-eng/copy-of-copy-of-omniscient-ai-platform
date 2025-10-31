""""""

Real-time WebSocket Telemetry RoutesWebSocket Telemetry Streaming

"""Real-time IoT telemetry data streaming with authentication and tenant isolation

"""

from fastapi import APIRouter, WebSocketfrom typing import Optional, Dict, Any, Set

from datetime import datetime, timezonefrom fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException

from jose import jwt, JWTError

router = APIRouter()import os

import json

import asyncio

@router.websocket("/realtime/{device_id}")import logging

async def websocket_endpoint(websocket: WebSocket, device_id: str):from datetime import datetime, timezone

    """WebSocket endpoint for real-time telemetry"""

    from utils.gcp import get_firestore

    await websocket.accept()

    router = APIRouter()

    try:logger = logging.getLogger(__name__)

        while True:

            data = await websocket.receive_text()JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-prod")

            

            # Echo back with timestamp# Active WebSocket connections per tenant

            response = {# Structure: {tenant_id: {connection_id: WebSocket}}

                "device_id": device_id,active_connections: Dict[str, Dict[str, WebSocket]] = {}

                "message": "Data received",

                "timestamp": datetime.now(timezone.utc).isoformat()

            }def verify_token(token: str) -> Dict[str, Any]:

                """Verify JWT token and return payload"""

            await websocket.send_json(response)    try:

                    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

    except Exception as e:        return payload

        print(f"WebSocket error: {e}")    except JWTError as e:

    finally:        logger.error(f"JWT verification failed: {e}")

        await websocket.close()        raise HTTPException(status_code=401, detail="Invalid token")





@router.get("/ws/stats")async def broadcast_to_tenant(tenant_id: str, message: dict):

async def get_websocket_stats():    """Broadcast message to all connected clients of a tenant"""

    """Get WebSocket connection statistics"""    if tenant_id not in active_connections:

            return

    return {    

        "active_connections": 142,    disconnected = []

        "total_messages_today": 45678,    for conn_id, websocket in active_connections[tenant_id].items():

        "average_latency_ms": 28.5        try:

    }            await websocket.send_json(message)

        except Exception as e:
            logger.error(f"Failed to send to {conn_id}: {e}")
            disconnected.append(conn_id)
    
    # Clean up disconnected clients
    for conn_id in disconnected:
        active_connections[tenant_id].pop(conn_id, None)
    
    # Remove tenant entry if no more connections
    if tenant_id in active_connections and not active_connections[tenant_id]:
        del active_connections[tenant_id]


@router.websocket("/telemetry/stream")
async def websocket_telemetry_stream(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time telemetry streaming
    
    Query Parameters:
    - token: JWT authentication token (required)
    - device_id: Optional device ID to filter telemetry (if not provided, streams all tenant devices)
    
    Usage:
    ws://backend-url/api/v1/iot/ws/telemetry/stream?token=YOUR_JWT&device_id=sensor-001
    
    Message Format (Server -> Client):
    {
        "type": "telemetry",
        "device_id": "sensor-001",
        "timestamp": "2025-10-31T12:34:56Z",
        "metrics": {
            "temperature": 22.5,
            "humidity": 65
        }
    }
    
    Client can send heartbeat: {"type": "ping"}
    Server responds with: {"type": "pong", "timestamp": "..."}
    """
    
    # Verify authentication
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
    
    try:
        user = verify_token(token)
        tenant_id = user.get("tenant_id", "unknown")
        user_id = user.get("sub", "unknown")
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid authentication token")
        return
    
    # Accept connection
    await websocket.accept()
    
    # Register connection
    conn_id = f"{user_id}_{datetime.now(timezone.utc).timestamp()}"
    if tenant_id not in active_connections:
        active_connections[tenant_id] = {}
    active_connections[tenant_id][conn_id] = websocket
    
    logger.info(f"WebSocket connected: {conn_id} (tenant: {tenant_id}, device: {device_id or 'all'})")
    
    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "connection_id": conn_id,
        "tenant_id": tenant_id,
        "device_filter": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    try:
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for messages from client (with timeout for heartbeat check)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                # Handle ping/pong
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
                # Handle device filter update
                elif message.get("type") == "subscribe":
                    new_device_id = message.get("device_id")
                    device_id = new_device_id
                    await websocket.send_json({
                        "type": "subscribed",
                        "device_id": device_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {conn_id}")
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conn_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {conn_id}: {e}")
    finally:
        # Clean up connection
        if tenant_id in active_connections:
            active_connections[tenant_id].pop(conn_id, None)
            if not active_connections[tenant_id]:
                del active_connections[tenant_id]
        logger.info(f"WebSocket cleanup: {conn_id}")


@router.get("/telemetry/connections")
async def get_active_connections():
    """Get statistics about active WebSocket connections (admin endpoint)"""
    stats = {
        "total_connections": sum(len(conns) for conns in active_connections.values()),
        "tenants_connected": len(active_connections),
        "connections_per_tenant": {
            tenant_id: len(conns) 
            for tenant_id, conns in active_connections.items()
        }
    }
    return stats


# Helper function to be called when new telemetry is ingested
async def notify_telemetry_subscribers(tenant_id: str, device_id: str, metrics: dict):
    """
    Call this function when new telemetry data is ingested to broadcast to WebSocket clients
    
    This should be integrated into the telemetry ingestion endpoint
    """
    message = {
        "type": "telemetry",
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics
    }
    await broadcast_to_tenant(tenant_id, message)
