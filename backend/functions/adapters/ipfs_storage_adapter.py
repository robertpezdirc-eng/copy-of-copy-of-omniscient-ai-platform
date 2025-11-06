import os
import json
import time
import hashlib
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List, Union, BinaryIO
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class IPFSObject:
    """Predstavlja objekt shranjen v IPFS"""
    hash: str
    name: str
    size: int
    type: str  # "file", "directory", "model", "dataset"
    metadata: Dict[str, Any]
    created_at: float
    pinned: bool = False

@dataclass
class ModelSnapshot:
    """Posnetek modela za shranjevanje v IPFS"""
    model_id: str
    version: str
    model_data: Dict[str, Any]
    training_metadata: Dict[str, Any]
    performance_metrics: Dict[str, float]
    federated_round: Optional[int] = None

class IPFSStorageAdapter:
    """
    Adapter za decentralizirano shranjevanje v IPFS.
    Omogoča shranjevanje modelov, podatkov za učenje in federativnih posodobitev.
    """
    
    def __init__(self, 
                 ipfs_api_url: Optional[str] = None,
                 ipfs_gateway_url: Optional[str] = None):
        self.api_url = ipfs_api_url or os.getenv("IPFS_API_URL", "http://localhost:5001")
        self.gateway_url = ipfs_gateway_url or os.getenv("IPFS_GATEWAY_URL", "http://localhost:8080")
        
        # Lokalni cache za IPFS objekte
        self.cache: Dict[str, IPFSObject] = {}
        self.cache_dir = Path(os.getenv("IPFS_CACHE_DIR", "./data/ipfs_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Konfiguracija
        self.auto_pin = os.getenv("IPFS_AUTO_PIN", "true").lower() == "true"
        self.max_cache_size = int(os.getenv("IPFS_MAX_CACHE_SIZE", "1000"))
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Izvede HTTP zahtevo na IPFS API"""
        url = f"{self.api_url}/api/v0/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"IPFS API napaka {response.status}: {error_text}")
        except aiohttp.ClientError as e:
            raise Exception(f"Napaka pri povezavi z IPFS: {e}")
    
    async def add_file(self, 
                      file_path: Union[str, Path], 
                      name: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> IPFSObject:
        """Doda datoteko v IPFS"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Datoteka ne obstaja: {file_path}")
        
        name = name or file_path.name
        metadata = metadata or {}
        
        try:
            # Preberi datoteko
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=name)
                
                # Dodaj v IPFS
                result = await self._make_request('POST', 'add', data=data)
                
                ipfs_hash = result['Hash']
                size = int(result['Size'])
                
                # Ustvari IPFS objekt
                ipfs_obj = IPFSObject(
                    hash=ipfs_hash,
                    name=name,
                    size=size,
                    type="file",
                    metadata=metadata,
                    created_at=time.time(),
                    pinned=False
                )
                
                # Avtomatsko pripni, če je omogočeno
                if self.auto_pin:
                    await self.pin_object(ipfs_hash)
                    ipfs_obj.pinned = True
                
                # Dodaj v cache
                self.cache[ipfs_hash] = ipfs_obj
                await self._save_cache()
                
                return ipfs_obj
                
        except Exception as e:
            raise Exception(f"Napaka pri dodajanju datoteke v IPFS: {e}")
    
    async def add_json(self, 
                      data: Dict[str, Any], 
                      name: str,
                      metadata: Optional[Dict[str, Any]] = None) -> IPFSObject:
        """Doda JSON podatke v IPFS"""
        try:
            # Pretvori v JSON string
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Ustvari začasno datoteko
            temp_file = self.cache_dir / f"temp_{int(time.time())}_{name}.json"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(json_data)
            
            # Dodaj v IPFS
            ipfs_obj = await self.add_file(temp_file, name, metadata)
            ipfs_obj.type = "json"
            
            # Počisti začasno datoteko
            temp_file.unlink()
            
            return ipfs_obj
            
        except Exception as e:
            raise Exception(f"Napaka pri dodajanju JSON v IPFS: {e}")
    
    async def store_model_snapshot(self, snapshot: ModelSnapshot) -> IPFSObject:
        """Shrani posnetek modela v IPFS"""
        try:
            # Pripravi metadata
            metadata = {
                "type": "model_snapshot",
                "model_id": snapshot.model_id,
                "version": snapshot.version,
                "federated_round": snapshot.federated_round,
                "performance_metrics": snapshot.performance_metrics,
                "training_metadata": snapshot.training_metadata
            }
            
            # Pretvori v JSON format
            snapshot_data = {
                "model_id": snapshot.model_id,
                "version": snapshot.version,
                "model_data": snapshot.model_data,
                "training_metadata": snapshot.training_metadata,
                "performance_metrics": snapshot.performance_metrics,
                "federated_round": snapshot.federated_round,
                "timestamp": time.time()
            }
            
            name = f"model_{snapshot.model_id}_{snapshot.version}.json"
            
            # Shrani v IPFS
            ipfs_obj = await self.add_json(snapshot_data, name, metadata)
            ipfs_obj.type = "model"
            
            return ipfs_obj
            
        except Exception as e:
            raise Exception(f"Napaka pri shranjevanju modela: {e}")
    
    async def get_object(self, ipfs_hash: str) -> Optional[bytes]:
        """Pridobi objekt iz IPFS"""
        try:
            # Preveri cache
            cache_file = self.cache_dir / f"{ipfs_hash}.cache"
            if cache_file.exists():
                return cache_file.read_bytes()
            
            # Pridobi iz IPFS
            url = f"{self.gateway_url}/ipfs/{ipfs_hash}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        
                        # Shrani v cache
                        cache_file.write_bytes(data)
                        
                        return data
                    else:
                        return None
                        
        except Exception as e:
            print(f"Napaka pri pridobivanju objekta {ipfs_hash}: {e}")
            return None
    
    async def get_json(self, ipfs_hash: str) -> Optional[Dict[str, Any]]:
        """Pridobi JSON objekt iz IPFS"""
        try:
            data = await self.get_object(ipfs_hash)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            print(f"Napaka pri pridobivanju JSON objekta {ipfs_hash}: {e}")
            return None
    
    async def load_model_snapshot(self, ipfs_hash: str) -> Optional[ModelSnapshot]:
        """Naloži posnetek modela iz IPFS"""
        try:
            data = await self.get_json(ipfs_hash)
            if not data:
                return None
            
            return ModelSnapshot(
                model_id=data["model_id"],
                version=data["version"],
                model_data=data["model_data"],
                training_metadata=data["training_metadata"],
                performance_metrics=data["performance_metrics"],
                federated_round=data.get("federated_round")
            )
            
        except Exception as e:
            print(f"Napaka pri nalaganju modela {ipfs_hash}: {e}")
            return None
    
    async def pin_object(self, ipfs_hash: str) -> bool:
        """Pripni objekt v IPFS (prepreči garbage collection)"""
        try:
            await self._make_request('POST', f'pin/add?arg={ipfs_hash}')
            
            # Posodobi cache
            if ipfs_hash in self.cache:
                self.cache[ipfs_hash].pinned = True
                await self._save_cache()
            
            return True
        except Exception as e:
            print(f"Napaka pri pripenjanju objekta {ipfs_hash}: {e}")
            return False
    
    async def unpin_object(self, ipfs_hash: str) -> bool:
        """Odpni objekt v IPFS"""
        try:
            await self._make_request('POST', f'pin/rm?arg={ipfs_hash}')
            
            # Posodobi cache
            if ipfs_hash in self.cache:
                self.cache[ipfs_hash].pinned = False
                await self._save_cache()
            
            return True
        except Exception as e:
            print(f"Napaka pri odpenjanju objekta {ipfs_hash}: {e}")
            return False
    
    async def list_pinned_objects(self) -> List[str]:
        """Vrne seznam pripetih objektov"""
        try:
            result = await self._make_request('POST', 'pin/ls')
            return list(result.get('Keys', {}).keys())
        except Exception as e:
            print(f"Napaka pri pridobivanju pripetih objektov: {e}")
            return []
    
    async def get_node_info(self) -> Dict[str, Any]:
        """Pridobi informacije o IPFS vozlišču"""
        try:
            id_info = await self._make_request('POST', 'id')
            stats = await self._make_request('POST', 'stats/repo')
            
            return {
                "node_id": id_info.get("ID"),
                "agent_version": id_info.get("AgentVersion"),
                "protocol_version": id_info.get("ProtocolVersion"),
                "addresses": id_info.get("Addresses", []),
                "repo_size": stats.get("RepoSize", 0),
                "storage_max": stats.get("StorageMax", 0),
                "num_objects": stats.get("NumObjects", 0)
            }
        except Exception as e:
            print(f"Napaka pri pridobivanju informacij o vozlišču: {e}")
            return {}
    
    async def search_models(self, 
                           model_id: Optional[str] = None,
                           version_pattern: Optional[str] = None,
                           min_performance: Optional[float] = None) -> List[IPFSObject]:
        """Poišče modele v cache glede na kriterije"""
        results = []
        
        for ipfs_obj in self.cache.values():
            if ipfs_obj.type != "model":
                continue
            
            metadata = ipfs_obj.metadata
            
            # Filtriraj po model_id
            if model_id and metadata.get("model_id") != model_id:
                continue
            
            # Filtriraj po verziji
            if version_pattern and version_pattern not in metadata.get("version", ""):
                continue
            
            # Filtriraj po performansah
            if min_performance:
                metrics = metadata.get("performance_metrics", {})
                max_metric = max(metrics.values()) if metrics else 0.0
                if max_metric < min_performance:
                    continue
            
            results.append(ipfs_obj)
        
        # Sortiraj po času nastanka (najnovejši prvi)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results
    
    async def cleanup_cache(self, max_age_days: int = 30) -> int:
        """Počisti stare cache datoteke"""
        cleaned_count = 0
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                if current_time - cache_file.stat().st_mtime > max_age_seconds:
                    cache_file.unlink()
                    cleaned_count += 1
            
            # Počisti tudi cache objekte
            to_remove = []
            for ipfs_hash, ipfs_obj in self.cache.items():
                if current_time - ipfs_obj.created_at > max_age_seconds:
                    to_remove.append(ipfs_hash)
            
            for ipfs_hash in to_remove:
                del self.cache[ipfs_hash]
                cleaned_count += 1
            
            if to_remove:
                await self._save_cache()
            
        except Exception as e:
            print(f"Napaka pri čiščenju cache: {e}")
        
        return cleaned_count
    
    async def _save_cache(self) -> None:
        """Shrani cache na disk"""
        try:
            cache_file = self.cache_dir / "ipfs_cache.json"
            cache_data = {
                hash: asdict(obj) for hash, obj in self.cache.items()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Napaka pri shranjevanju cache: {e}")
    
    async def _load_cache(self) -> None:
        """Naloži cache z diska"""
        try:
            cache_file = self.cache_dir / "ipfs_cache.json"
            
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                self.cache = {
                    hash: IPFSObject(**obj_data) 
                    for hash, obj_data in cache_data.items()
                }
                
        except Exception as e:
            print(f"Napaka pri nalaganju cache: {e}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Pridobi statistike shranjevanja"""
        try:
            node_info = await self.get_node_info()
            pinned_objects = await self.list_pinned_objects()
            
            # Statistike cache
            cache_size = sum(obj.size for obj in self.cache.values())
            model_count = len([obj for obj in self.cache.values() if obj.type == "model"])
            
            return {
                "node_info": node_info,
                "pinned_objects_count": len(pinned_objects),
                "cache_objects_count": len(self.cache),
                "cache_size_bytes": cache_size,
                "model_snapshots_count": model_count,
                "cache_directory": str(self.cache_dir),
                "auto_pin_enabled": self.auto_pin
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def initialize(self) -> bool:
        """Inicializira IPFS adapter"""
        try:
            # Naloži cache
            await self._load_cache()
            
            # Preveri povezavo z IPFS
            node_info = await self.get_node_info()
            if not node_info:
                return False
            
            print(f"IPFS adapter inicializiran. Vozlišče: {node_info.get('node_id', 'neznano')}")
            return True
            
        except Exception as e:
            print(f"Napaka pri inicializaciji IPFS adapterja: {e}")
            return False