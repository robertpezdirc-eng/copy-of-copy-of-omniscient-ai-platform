import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Set, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from urllib.parse import urlparse
import numpy as np
from collections import deque, defaultdict

# Konfiguracija logiranja
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SensorDataType(Enum):
    """Tipi senzorskih podatkov"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    MOTION = "motion"
    LIGHT = "light"
    SOUND = "sound"
    GPS = "gps"
    ACCELEROMETER = "accelerometer"
    GYROSCOPE = "gyroscope"
    MAGNETOMETER = "magnetometer"
    CUSTOM = "custom"

@dataclass
class SensorReading:
    """Posamezno branje senzorja"""
    sensor_id: str
    sensor_type: SensorDataType
    value: Union[float, int, Dict[str, Any], List[Any]]
    unit: str
    timestamp: float
    location: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None
    quality_score: float = 1.0

@dataclass
class SensorStream:
    """Definicija senzorskega toka"""
    stream_id: str
    websocket_url: str
    sensor_types: List[SensorDataType]
    sampling_rate_hz: float
    buffer_size: int = 1000
    auto_reconnect: bool = True
    auth_headers: Optional[Dict[str, str]] = None
    data_format: str = "json"  # json, binary, csv
    compression: Optional[str] = None  # gzip, lz4

@dataclass
class StreamStatistics:
    """Statistike toka"""
    total_messages: int = 0
    messages_per_second: float = 0.0
    bytes_received: int = 0
    last_message_time: float = 0.0
    connection_uptime: float = 0.0
    reconnection_count: int = 0
    error_count: int = 0
    data_quality_avg: float = 1.0

class DataProcessor:
    """Procesor za real-time obdelavo podatkov"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.data_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.processors: Dict[str, List[Callable]] = defaultdict(list)
        
    def add_processor(self, sensor_type: str, processor: Callable[[List[SensorReading]], Any]):
        """Dodaj procesor za določen tip senzorja"""
        self.processors[sensor_type].append(processor)
    
    async def process_reading(self, reading: SensorReading) -> Dict[str, Any]:
        """Obdelaj novo branje"""
        sensor_key = f"{reading.sensor_id}_{reading.sensor_type.value}"
        self.data_windows[sensor_key].append(reading)
        
        results = {}
        
        # Izvedi vse procesore za ta tip senzorja
        for processor in self.processors[reading.sensor_type.value]:
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, processor, list(self.data_windows[sensor_key])
                )
                results[processor.__name__] = result
            except Exception as e:
                logger.error(f"Napaka pri obdelavi {processor.__name__}: {e}")
        
        return results

class AnomalyDetector:
    """Detektor anomalij v senzorskih podatkih"""
    
    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity
        self.baselines: Dict[str, Dict[str, float]] = {}
        self.anomaly_counts: Dict[str, int] = defaultdict(int)
    
    def update_baseline(self, sensor_id: str, readings: List[SensorReading]):
        """Posodobi baseline za senzor"""
        if not readings:
            return
        
        values = [r.value for r in readings if isinstance(r.value, (int, float))]
        if not values:
            return
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        self.baselines[sensor_id] = {
            "mean": mean_val,
            "std": std_val,
            "min": min(values),
            "max": max(values),
            "updated": time.time()
        }
    
    def detect_anomaly(self, reading: SensorReading) -> Dict[str, Any]:
        """Zazna anomalije v branju"""
        sensor_id = reading.sensor_id
        
        if sensor_id not in self.baselines:
            return {"is_anomaly": False, "reason": "no_baseline"}
        
        baseline = self.baselines[sensor_id]
        
        if not isinstance(reading.value, (int, float)):
            return {"is_anomaly": False, "reason": "non_numeric"}
        
        # Z-score anomaly detection
        z_score = abs(reading.value - baseline["mean"]) / (baseline["std"] + 1e-8)
        is_anomaly = z_score > self.sensitivity
        
        if is_anomaly:
            self.anomaly_counts[sensor_id] += 1
        
        return {
            "is_anomaly": is_anomaly,
            "z_score": z_score,
            "threshold": self.sensitivity,
            "baseline_mean": baseline["mean"],
            "baseline_std": baseline["std"],
            "anomaly_count": self.anomaly_counts[sensor_id]
        }

class WebSocketSensorAdapter:
    """
    WebSocket adapter za real-time senzorske podatke.
    Razširi NetAgent z zmožnostmi streaming obdelave.
    """
    
    def __init__(self):
        # Konfiguracija
        self.max_connections = int(os.getenv("WEBSOCKET_MAX_CONNECTIONS", "50"))
        self.connection_timeout = int(os.getenv("WEBSOCKET_TIMEOUT", "30"))
        self.max_message_size = int(os.getenv("WEBSOCKET_MAX_MESSAGE_SIZE", "1048576"))
        self.enable_compression = os.getenv("WEBSOCKET_ENABLE_COMPRESSION", "1") == "1"
        
        # Stanje
        self.active_streams: Dict[str, SensorStream] = {}
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.statistics: Dict[str, StreamStatistics] = {}
        self.data_processor = DataProcessor()
        self.anomaly_detector = AnomalyDetector()
        
        # Event handlers
        self.message_handlers: List[Callable[[str, SensorReading], None]] = []
        self.anomaly_handlers: List[Callable[[str, SensorReading, Dict[str, Any]], None]] = []
        self.connection_handlers: List[Callable[[str, str], None]] = []  # stream_id, event_type
        
        # Buffer za batch processing
        self.message_buffer: Dict[str, List[SensorReading]] = defaultdict(list)
        self.buffer_flush_interval = float(os.getenv("BUFFER_FLUSH_INTERVAL", "1.0"))
        
        # Inicializiraj osnovne procesore
        self._setup_default_processors()
    
    def _setup_default_processors(self):
        """Nastavi osnovne procesore podatkov"""
        
        def moving_average(readings: List[SensorReading]) -> float:
            """Drseče povprečje"""
            values = [r.value for r in readings if isinstance(r.value, (int, float))]
            return sum(values) / len(values) if values else 0.0
        
        def trend_analysis(readings: List[SensorReading]) -> Dict[str, Any]:
            """Analiza trenda"""
            if len(readings) < 2:
                return {"trend": "insufficient_data"}
            
            values = [r.value for r in readings if isinstance(r.value, (int, float))]
            if len(values) < 2:
                return {"trend": "non_numeric"}
            
            # Enostavna linearna regresija
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            if slope > 0.1:
                trend = "increasing"
            elif slope < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "trend": trend,
                "slope": slope,
                "change_rate": slope * len(values)
            }
        
        def quality_assessment(readings: List[SensorReading]) -> Dict[str, Any]:
            """Ocena kakovosti podatkov"""
            if not readings:
                return {"quality": 0.0}
            
            # Preveri konsistentnost časovnih žigov
            timestamps = [r.timestamp for r in readings]
            time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            
            expected_interval = 1.0 / 10.0  # Predpostavljamo 10 Hz
            time_consistency = 1.0 - (np.std(time_diffs) / expected_interval) if time_diffs else 1.0
            time_consistency = max(0.0, min(1.0, time_consistency))
            
            # Povprečna kakovost
            avg_quality = sum(r.quality_score for r in readings) / len(readings)
            
            overall_quality = (time_consistency + avg_quality) / 2.0
            
            return {
                "quality": overall_quality,
                "time_consistency": time_consistency,
                "avg_sensor_quality": avg_quality,
                "sample_count": len(readings)
            }
        
        # Registriraj procesore za vse tipe senzorjev
        for sensor_type in SensorDataType:
            self.data_processor.add_processor(sensor_type.value, moving_average)
            self.data_processor.add_processor(sensor_type.value, trend_analysis)
            self.data_processor.add_processor(sensor_type.value, quality_assessment)
    
    def add_message_handler(self, handler: Callable[[str, SensorReading], None]):
        """Dodaj handler za sporočila"""
        self.message_handlers.append(handler)
    
    def add_anomaly_handler(self, handler: Callable[[str, SensorReading, Dict[str, Any]], None]):
        """Dodaj handler za anomalije"""
        self.anomaly_handlers.append(handler)
    
    def add_connection_handler(self, handler: Callable[[str, str], None]):
        """Dodaj handler za povezave"""
        self.connection_handlers.append(handler)
    
    async def create_stream(self, stream_config: SensorStream) -> bool:
        """Ustvari nov senzorski tok"""
        try:
            # Preveri URL
            parsed = urlparse(stream_config.websocket_url)
            if parsed.scheme not in ("ws", "wss"):
                logger.error(f"Nepodprt protokol: {parsed.scheme}")
                return False
            
            # Preveri omejitve
            if len(self.active_streams) >= self.max_connections:
                logger.error("Dosežena maksimalna število povezav")
                return False
            
            # Registriraj tok
            self.active_streams[stream_config.stream_id] = stream_config
            self.statistics[stream_config.stream_id] = StreamStatistics()
            
            # Zaženi povezavo
            asyncio.create_task(self._maintain_connection(stream_config))
            
            logger.info(f"Ustvarjen tok {stream_config.stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"Napaka pri ustvarjanju toka {stream_config.stream_id}: {e}")
            return False
    
    async def _maintain_connection(self, stream_config: SensorStream):
        """Vzdržuje WebSocket povezavo z avtomatskim reconnect"""
        stream_id = stream_config.stream_id
        reconnect_delay = 1.0
        max_reconnect_delay = 60.0
        
        while stream_id in self.active_streams:
            try:
                # Pripravi headers
                extra_headers = stream_config.auth_headers or {}
                
                # Vzpostavi povezavo
                logger.info(f"Povezujem se na {stream_config.websocket_url}")
                
                async with websockets.connect(
                    stream_config.websocket_url,
                    extra_headers=extra_headers,
                    max_size=self.max_message_size,
                    compression="deflate" if self.enable_compression else None,
                    ping_interval=20,
                    ping_timeout=10
                ) as websocket:
                    
                    self.connections[stream_id] = websocket
                    self.statistics[stream_id].connection_uptime = time.time()
                    reconnect_delay = 1.0  # Reset delay po uspešni povezavi
                    
                    # Obvesti o povezavi
                    for handler in self.connection_handlers:
                        try:
                            handler(stream_id, "connected")
                        except Exception as e:
                            logger.error(f"Napaka v connection handler: {e}")
                    
                    # Poslušaj sporočila
                    await self._listen_messages(websocket, stream_config)
                    
            except ConnectionClosed:
                logger.warning(f"Povezava {stream_id} zaprta")
            except WebSocketException as e:
                logger.error(f"WebSocket napaka za {stream_id}: {e}")
            except Exception as e:
                logger.error(f"Nepričakovana napaka za {stream_id}: {e}")
            
            finally:
                # Počisti povezavo
                if stream_id in self.connections:
                    del self.connections[stream_id]
                
                self.statistics[stream_id].reconnection_count += 1
                
                # Obvesti o prekinitvi
                for handler in self.connection_handlers:
                    try:
                        handler(stream_id, "disconnected")
                    except Exception as e:
                        logger.error(f"Napaka v connection handler: {e}")
            
            # Avtomatski reconnect
            if stream_config.auto_reconnect and stream_id in self.active_streams:
                logger.info(f"Ponovno povezovanje za {stream_id} čez {reconnect_delay}s")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
            else:
                break
    
    async def _listen_messages(self, websocket: websockets.WebSocketServerProtocol, stream_config: SensorStream):
        """Posluša sporočila iz WebSocket povezave"""
        stream_id = stream_config.stream_id
        stats = self.statistics[stream_id]
        
        try:
            async for message in websocket:
                try:
                    # Posodobi statistike
                    stats.total_messages += 1
                    stats.bytes_received += len(message) if isinstance(message, (str, bytes)) else 0
                    stats.last_message_time = time.time()
                    
                    # Izračunaj sporočila na sekundo
                    if stats.total_messages > 1:
                        uptime = time.time() - stats.connection_uptime
                        stats.messages_per_second = stats.total_messages / uptime
                    
                    # Parsiraj sporočilo
                    reading = await self._parse_message(message, stream_config)
                    if not reading:
                        continue
                    
                    # Dodaj v buffer
                    self.message_buffer[stream_id].append(reading)
                    
                    # Obdelaj sporočilo
                    await self._process_reading(stream_id, reading)
                    
                except Exception as e:
                    logger.error(f"Napaka pri obdelavi sporočila za {stream_id}: {e}")
                    stats.error_count += 1
                    
        except ConnectionClosed:
            logger.info(f"Povezava {stream_id} zaprta normalno")
        except Exception as e:
            logger.error(f"Napaka pri poslušanju {stream_id}: {e}")
            stats.error_count += 1
    
    async def _parse_message(self, message: Union[str, bytes], stream_config: SensorStream) -> Optional[SensorReading]:
        """Parsiraj sporočilo v SensorReading"""
        try:
            if stream_config.data_format == "json":
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                
                data = json.loads(message)
                
                # Pričakujemo strukturo:
                # {
                #   "sensor_id": "temp_01",
                #   "sensor_type": "temperature",
                #   "value": 23.5,
                #   "unit": "°C",
                #   "timestamp": 1234567890.123,
                #   "location": {"lat": 46.0569, "lon": 14.5058},
                #   "metadata": {"device": "DHT22"},
                #   "quality_score": 0.95
                # }
                
                sensor_type = SensorDataType(data.get("sensor_type", "custom"))
                
                reading = SensorReading(
                    sensor_id=data["sensor_id"],
                    sensor_type=sensor_type,
                    value=data["value"],
                    unit=data.get("unit", ""),
                    timestamp=data.get("timestamp", time.time()),
                    location=data.get("location"),
                    metadata=data.get("metadata"),
                    quality_score=data.get("quality_score", 1.0)
                )
                
                return reading
                
            elif stream_config.data_format == "csv":
                # Enostavno CSV parsing
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                
                parts = message.strip().split(',')
                if len(parts) >= 4:
                    return SensorReading(
                        sensor_id=parts[0],
                        sensor_type=SensorDataType(parts[1]) if parts[1] in [t.value for t in SensorDataType] else SensorDataType.CUSTOM,
                        value=float(parts[2]),
                        unit=parts[3],
                        timestamp=float(parts[4]) if len(parts) > 4 else time.time(),
                        quality_score=float(parts[5]) if len(parts) > 5 else 1.0
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Napaka pri parsiranju sporočila: {e}")
            return None
    
    async def _process_reading(self, stream_id: str, reading: SensorReading):
        """Obdelaj branje senzorja"""
        try:
            # Obdelaj podatke
            processing_results = await self.data_processor.process_reading(reading)
            
            # Zazna anomalije
            anomaly_result = self.anomaly_detector.detect_anomaly(reading)
            
            # Posodobi baseline
            if len(self.data_processor.data_windows[f"{reading.sensor_id}_{reading.sensor_type.value}"]) >= 50:
                readings_list = list(self.data_processor.data_windows[f"{reading.sensor_id}_{reading.sensor_type.value}"])
                self.anomaly_detector.update_baseline(reading.sensor_id, readings_list)
            
            # Obvesti message handlers
            for handler in self.message_handlers:
                try:
                    handler(stream_id, reading)
                except Exception as e:
                    logger.error(f"Napaka v message handler: {e}")
            
            # Obvesti anomaly handlers, če je anomalija
            if anomaly_result.get("is_anomaly", False):
                for handler in self.anomaly_handlers:
                    try:
                        handler(stream_id, reading, anomaly_result)
                    except Exception as e:
                        logger.error(f"Napaka v anomaly handler: {e}")
            
            # Posodobi kakovost podatkov
            quality = processing_results.get("quality_assessment", {}).get("quality", 1.0)
            stats = self.statistics[stream_id]
            stats.data_quality_avg = (stats.data_quality_avg * 0.9) + (quality * 0.1)
            
        except Exception as e:
            logger.error(f"Napaka pri obdelavi branja: {e}")
    
    async def remove_stream(self, stream_id: str) -> bool:
        """Odstrani senzorski tok"""
        try:
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
            
            if stream_id in self.connections:
                await self.connections[stream_id].close()
                del self.connections[stream_id]
            
            if stream_id in self.statistics:
                del self.statistics[stream_id]
            
            if stream_id in self.message_buffer:
                del self.message_buffer[stream_id]
            
            logger.info(f"Odstranjen tok {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"Napaka pri odstranjevanju toka {stream_id}: {e}")
            return False
    
    async def get_stream_statistics(self, stream_id: Optional[str] = None) -> Dict[str, Any]:
        """Vrne statistike tokov"""
        if stream_id:
            if stream_id in self.statistics:
                stats = self.statistics[stream_id]
                return {
                    "stream_id": stream_id,
                    "statistics": asdict(stats),
                    "is_connected": stream_id in self.connections,
                    "buffer_size": len(self.message_buffer.get(stream_id, [])),
                    "active": stream_id in self.active_streams
                }
            else:
                return {"error": "stream_not_found"}
        else:
            return {
                "total_streams": len(self.active_streams),
                "active_connections": len(self.connections),
                "streams": {
                    sid: {
                        "statistics": asdict(stats),
                        "is_connected": sid in self.connections,
                        "buffer_size": len(self.message_buffer.get(sid, []))
                    }
                    for sid, stats in self.statistics.items()
                }
            }
    
    async def send_command(self, stream_id: str, command: Dict[str, Any]) -> bool:
        """Pošlje ukaz preko WebSocket povezave"""
        try:
            if stream_id not in self.connections:
                return False
            
            websocket = self.connections[stream_id]
            await websocket.send(json.dumps(command))
            return True
            
        except Exception as e:
            logger.error(f"Napaka pri pošiljanju ukaza za {stream_id}: {e}")
            return False
    
    async def get_recent_readings(self, stream_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Vrne nedavna branja za tok"""
        try:
            if stream_id not in self.message_buffer:
                return []
            
            readings = list(self.message_buffer[stream_id])[-limit:]
            return [asdict(reading) for reading in readings]
            
        except Exception as e:
            logger.error(f"Napaka pri pridobivanju branj za {stream_id}: {e}")
            return []
    
    async def flush_buffers(self):
        """Izprazni vse bufferje (za batch processing)"""
        try:
            for stream_id, readings in self.message_buffer.items():
                if readings:
                    logger.info(f"Flushing {len(readings)} readings for {stream_id}")
                    # Tu bi lahko implementirali batch processing
                    readings.clear()
                    
        except Exception as e:
            logger.error(f"Napaka pri flushing bufferjev: {e}")
    
    async def start_buffer_flusher(self):
        """Zažene periodično praznjenje bufferjev"""
        while True:
            try:
                await asyncio.sleep(self.buffer_flush_interval)
                await self.flush_buffers()
            except Exception as e:
                logger.error(f"Napaka v buffer flusher: {e}")
                await asyncio.sleep(5)
    
    async def shutdown(self):
        """Zapre vse povezave in počisti resurse"""
        logger.info("Zapiranje WebSocket Sensor Adapter...")
        
        # Zapri vse povezave
        for stream_id in list(self.active_streams.keys()):
            await self.remove_stream(stream_id)
        
        logger.info("WebSocket Sensor Adapter zaprt")