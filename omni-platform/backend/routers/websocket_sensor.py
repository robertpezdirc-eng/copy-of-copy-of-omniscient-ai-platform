from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import json
import asyncio
import time
from datetime import datetime

from adapters.websocket_sensor_adapter import (
    WebSocketSensorAdapter, 
    SensorStream, 
    SensorDataType, 
    SensorReading
)
from .access_controller import require_api_key

router = APIRouter(prefix="/websocket-sensors", tags=["websocket-sensors"])

# Globalna instanca adapterja
sensor_adapter = WebSocketSensorAdapter()

# Pydantic modeli
class CreateStreamRequest(BaseModel):
    stream_id: str = Field(..., description="Unikaten ID toka")
    websocket_url: str = Field(..., description="WebSocket URL senzorja")
    sensor_types: List[str] = Field(..., description="Seznam tipov senzorjev")
    sampling_rate_hz: float = Field(default=10.0, description="Frekvenca vzorčenja v Hz")
    buffer_size: int = Field(default=1000, description="Velikost bufferja")
    auto_reconnect: bool = Field(default=True, description="Avtomatsko ponovno povezovanje")
    auth_headers: Optional[Dict[str, str]] = Field(default=None, description="Avtentikacijski headerji")
    data_format: str = Field(default="json", description="Format podatkov (json, csv, binary)")
    compression: Optional[str] = Field(default=None, description="Kompresija (gzip, lz4)")

class SendCommandRequest(BaseModel):
    command: Dict[str, Any] = Field(..., description="Ukaz za pošiljanje")

class StreamResponse(BaseModel):
    success: bool
    message: str
    stream_id: Optional[str] = None

class StatisticsResponse(BaseModel):
    stream_id: Optional[str] = None
    statistics: Dict[str, Any]
    is_connected: bool
    buffer_size: int
    active: bool

class ReadingsResponse(BaseModel):
    stream_id: str
    readings: List[Dict[str, Any]]
    count: int

# WebSocket manager za real-time podatke
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.stream_subscriptions: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Odstrani iz vseh subscriptions
        for stream_id, connections in self.stream_subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)
    
    async def subscribe_to_stream(self, websocket: WebSocket, stream_id: str):
        if stream_id not in self.stream_subscriptions:
            self.stream_subscriptions[stream_id] = []
        self.stream_subscriptions[stream_id].append(websocket)
    
    async def broadcast_to_stream(self, stream_id: str, data: Dict[str, Any]):
        if stream_id in self.stream_subscriptions:
            disconnected = []
            for connection in self.stream_subscriptions[stream_id]:
                try:
                    await connection.send_text(json.dumps(data))
                except:
                    disconnected.append(connection)
            
            # Počisti prekinjena povezava
            for conn in disconnected:
                self.disconnect(conn)

ws_manager = WebSocketManager()

# Nastavi event handlers za sensor adapter
def setup_sensor_handlers():
    """Nastavi event handlers za senzorski adapter"""
    
    def on_message(stream_id: str, reading: SensorReading):
        """Handler za nova sporočila"""
        data = {
            "type": "sensor_reading",
            "stream_id": stream_id,
            "reading": {
                "sensor_id": reading.sensor_id,
                "sensor_type": reading.sensor_type.value,
                "value": reading.value,
                "unit": reading.unit,
                "timestamp": reading.timestamp,
                "location": reading.location,
                "metadata": reading.metadata,
                "quality_score": reading.quality_score
            },
            "timestamp": time.time()
        }
        
        # Broadcast vsem naročnikom
        asyncio.create_task(ws_manager.broadcast_to_stream(stream_id, data))
    
    def on_anomaly(stream_id: str, reading: SensorReading, anomaly_info: Dict[str, Any]):
        """Handler za anomalije"""
        data = {
            "type": "anomaly_detected",
            "stream_id": stream_id,
            "reading": {
                "sensor_id": reading.sensor_id,
                "sensor_type": reading.sensor_type.value,
                "value": reading.value,
                "unit": reading.unit,
                "timestamp": reading.timestamp
            },
            "anomaly_info": anomaly_info,
            "timestamp": time.time()
        }
        
        # Broadcast vsem naročnikom
        asyncio.create_task(ws_manager.broadcast_to_stream(stream_id, data))
        
        # Broadcast tudi na splošni anomaly kanal
        asyncio.create_task(ws_manager.broadcast_to_stream("anomalies", data))
    
    def on_connection_change(stream_id: str, event_type: str):
        """Handler za spremembe povezav"""
        data = {
            "type": "connection_event",
            "stream_id": stream_id,
            "event": event_type,
            "timestamp": time.time()
        }
        
        # Broadcast vsem naročnikom
        asyncio.create_task(ws_manager.broadcast_to_stream(stream_id, data))
    
    # Registriraj handlers
    sensor_adapter.add_message_handler(on_message)
    sensor_adapter.add_anomaly_handler(on_anomaly)
    sensor_adapter.add_connection_handler(on_connection_change)

# Inicializiraj handlers
setup_sensor_handlers()

@router.post("/streams", response_model=StreamResponse)
async def create_sensor_stream(
    request: CreateStreamRequest,
    auth: Dict[str, Any] = Depends(require_api_key)
) -> StreamResponse:
    """Ustvari nov senzorski tok"""
    try:
        # Validiraj sensor types
        sensor_types = []
        for st in request.sensor_types:
            try:
                sensor_types.append(SensorDataType(st))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Neveljaven tip senzorja: {st}")
        
        # Ustvari stream config
        stream_config = SensorStream(
            stream_id=request.stream_id,
            websocket_url=request.websocket_url,
            sensor_types=sensor_types,
            sampling_rate_hz=request.sampling_rate_hz,
            buffer_size=request.buffer_size,
            auto_reconnect=request.auto_reconnect,
            auth_headers=request.auth_headers,
            data_format=request.data_format,
            compression=request.compression
        )
        
        # Ustvari tok
        success = await sensor_adapter.create_stream(stream_config)
        
        if success:
            return StreamResponse(
                success=True,
                message="Tok uspešno ustvarjen",
                stream_id=request.stream_id
            )
        else:
            raise HTTPException(status_code=400, detail="Napaka pri ustvarjanju toka")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notranja napaka: {str(e)}")

@router.delete("/streams/{stream_id}", response_model=StreamResponse)
async def remove_sensor_stream(
    stream_id: str,
    auth: Dict[str, Any] = Depends(require_api_key)
) -> StreamResponse:
    """Odstrani senzorski tok"""
    try:
        success = await sensor_adapter.remove_stream(stream_id)
        
        if success:
            return StreamResponse(
                success=True,
                message="Tok uspešno odstranjen",
                stream_id=stream_id
            )
        else:
            raise HTTPException(status_code=404, detail="Tok ni najden")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notranja napaka: {str(e)}")

@router.get("/streams/{stream_id}/statistics", response_model=StatisticsResponse)
async def get_stream_statistics(
    stream_id: str,
    auth: Dict[str, Any] = Depends(require_api_key)
) -> StatisticsResponse:
    """Pridobi statistike toka"""
    try:
        stats = await sensor_adapter.get_stream_statistics(stream_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail="Tok ni najden")
        
        return StatisticsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notranja napaka: {str(e)}")

@router.get("/streams/statistics")
async def get_all_statistics(
    auth: Dict[str, Any] = Depends(require_api_key)
) -> Dict[str, Any]:
    """Pridobi statistike vseh tokov"""
    try:
        return await sensor_adapter.get_stream_statistics()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notranja napaka: {str(e)}")

@router.post("/streams/{stream_id}/command", response_model=StreamResponse)
async def send_stream_command(
    stream_id: str,
    request: SendCommandRequest,
    auth: Dict[str, Any] = Depends(require_api_key)
) -> StreamResponse:
    """Pošlje ukaz preko WebSocket povezave"""
    try:
        success = await sensor_adapter.send_command(stream_id, request.command)
        
        if success:
            return StreamResponse(
                success=True,
                message="Ukaz uspešno poslan",
                stream_id=stream_id
            )
        else:
            raise HTTPException(status_code=404, detail="Tok ni povezan")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notranja napaka: {str(e)}")

@router.get("/streams/{stream_id}/readings", response_model=ReadingsResponse)
async def get_recent_readings(
    stream_id: str,
    limit: int = 100,
    auth: Dict[str, Any] = Depends(require_api_key)
) -> ReadingsResponse:
    """Pridobi nedavna branja toka"""
    try:
        readings = await sensor_adapter.get_recent_readings(stream_id, limit)
        
        return ReadingsResponse(
            stream_id=stream_id,
            readings=readings,
            count=len(readings)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notranja napaka: {str(e)}")

@router.get("/sensor-types")
async def get_sensor_types(
    auth: Dict[str, Any] = Depends(require_api_key)
) -> Dict[str, List[str]]:
    """Vrne seznam podprtih tipov senzorjev"""
    return {
        "sensor_types": [sensor_type.value for sensor_type in SensorDataType]
    }

@router.websocket("/ws/{stream_id}")
async def websocket_stream_endpoint(websocket: WebSocket, stream_id: str):
    """WebSocket endpoint za real-time podatke toka"""
    await ws_manager.connect(websocket)
    await ws_manager.subscribe_to_stream(websocket, stream_id)
    
    try:
        # Pošlji pozdravno sporočilo
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "stream_id": stream_id,
            "timestamp": time.time()
        }))
        
        # Drži povezavo odprto
        while True:
            try:
                # Čakaj na sporočila od klienta (ping/pong, ukazi, itd.)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Obdelaj sporočilo
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": time.time()
                    }))
                elif message.get("type") == "subscribe_anomalies":
                    await ws_manager.subscribe_to_stream(websocket, "anomalies")
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "channel": "anomalies",
                        "timestamp": time.time()
                    }))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e),
                    "timestamp": time.time()
                }))
                
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)

@router.websocket("/ws/anomalies")
async def websocket_anomalies_endpoint(websocket: WebSocket):
    """WebSocket endpoint za anomalije vseh tokov"""
    await ws_manager.connect(websocket)
    await ws_manager.subscribe_to_stream(websocket, "anomalies")
    
    try:
        # Pošlji pozdravno sporočilo
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "channel": "anomalies",
            "timestamp": time.time()
        }))
        
        # Drži povezavo odprto
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": time.time()
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e),
                    "timestamp": time.time()
                }))
                
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)

@router.post("/flush-buffers")
async def flush_all_buffers(
    auth: Dict[str, Any] = Depends(require_api_key)
) -> StreamResponse:
    """Izprazni vse bufferje (za batch processing)"""
    try:
        await sensor_adapter.flush_buffers()
        return StreamResponse(
            success=True,
            message="Bufferji uspešno izpraznjeni"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notranja napaka: {str(e)}")

# Startup event za zagon buffer flusher
@router.on_event("startup")
async def startup_event():
    """Zaženi ozadnje naloge"""
    # Zaženi buffer flusher
    asyncio.create_task(sensor_adapter.start_buffer_flusher())

# Shutdown event za čiščenje
@router.on_event("shutdown")
async def shutdown_event():
    """Počisti resurse"""
    await sensor_adapter.shutdown()