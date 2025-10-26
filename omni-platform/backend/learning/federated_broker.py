import os
import time
import json
import asyncio
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, asdict
from .feedback_store import FeedbackStore
from .policy_manager import PolicyManager

@dataclass
class FederatedNode:
    """Predstavlja vozlišče v federativni mreži"""
    node_id: str
    endpoint: str
    last_seen: float
    model_version: str
    performance_score: float = 0.0
    is_active: bool = True

@dataclass
class ModelUpdate:
    """Predstavlja posodobitev modela od vozlišča"""
    node_id: str
    model_version: str
    gradient_hash: str
    performance_metrics: Dict[str, float]
    timestamp: float
    data_samples: int

@dataclass
class GlobalModel:
    """Globalni model v federativni mreži"""
    version: str
    model_hash: str
    aggregated_gradients: Dict[str, Any]
    participating_nodes: List[str]
    performance_metrics: Dict[str, float]
    created_at: float

class FederatedLearningBroker:
    """
    Koordinira federativno učenje med distribuiranimi vozlišči.
    Integrira se z obstoječo RL infrastrukturo (PolicyManager, FeedbackStore).
    """
    
    def __init__(self, 
                 node_id: Optional[str] = None,
                 store: Optional[FeedbackStore] = None,
                 policy_manager: Optional[PolicyManager] = None):
        self.node_id = node_id or self._generate_node_id()
        self.store = store or FeedbackStore()
        self.policy_manager = policy_manager or PolicyManager(self.store)
        
        # Federativno stanje
        self.nodes: Dict[str, FederatedNode] = {}
        self.pending_updates: List[ModelUpdate] = []
        self.global_model: Optional[GlobalModel] = None
        self.min_nodes_for_aggregation = int(os.getenv("FEDERATED_MIN_NODES", "3"))
        self.aggregation_interval = int(os.getenv("FEDERATED_AGGREGATION_INTERVAL", "300"))  # 5 min
        
        # Metrike
        self.total_rounds = 0
        self.successful_aggregations = 0
        
    def _generate_node_id(self) -> str:
        """Generira unikaten ID vozlišča"""
        hostname = os.getenv("HOSTNAME", "localhost")
        timestamp = str(int(time.time()))
        return hashlib.md5(f"{hostname}_{timestamp}".encode()).hexdigest()[:12]
    
    async def register_node(self, node: FederatedNode) -> bool:
        """Registrira novo vozlišče v federativni mreži"""
        try:
            self.nodes[node.node_id] = node
            
            # Logiraj registracijo v feedback store
            self.store.insert_event({
                "agent_type": "federated_broker",
                "task_type": "node_registration",
                "success": True,
                "reward": 1.0,
                "meta": {
                    "node_id": node.node_id,
                    "endpoint": node.endpoint,
                    "model_version": node.model_version
                }
            })
            
            return True
        except Exception as e:
            self.store.insert_event({
                "agent_type": "federated_broker",
                "task_type": "node_registration",
                "success": False,
                "reward": 0.0,
                "meta": {"error": str(e), "node_id": node.node_id}
            })
            return False
    
    async def submit_model_update(self, update: ModelUpdate) -> bool:
        """Sprejme posodobitev modela od vozlišča"""
        try:
            # Preveri, če je vozlišče registrirano
            if update.node_id not in self.nodes:
                return False
            
            # Posodobi zadnji čas aktivnosti vozlišča
            self.nodes[update.node_id].last_seen = time.time()
            
            # Dodaj posodobitev v čakalno vrsto
            self.pending_updates.append(update)
            
            # Logiraj posodobitev
            self.store.insert_event({
                "agent_type": "federated_broker",
                "task_type": "model_update_received",
                "success": True,
                "reward": self._calculate_update_reward(update),
                "meta": {
                    "node_id": update.node_id,
                    "model_version": update.model_version,
                    "data_samples": update.data_samples,
                    "performance_metrics": update.performance_metrics
                }
            })
            
            # Preveri, če lahko izvedemo agregacijo
            if len(self.pending_updates) >= self.min_nodes_for_aggregation:
                await self._trigger_aggregation()
            
            return True
        except Exception as e:
            self.store.insert_event({
                "agent_type": "federated_broker",
                "task_type": "model_update_received",
                "success": False,
                "reward": 0.0,
                "meta": {"error": str(e), "node_id": update.node_id}
            })
            return False
    
    def _calculate_update_reward(self, update: ModelUpdate) -> float:
        """Izračuna nagrado za posodobitev modela"""
        base_reward = 1.0
        
        # Bonus za večje število vzorcev
        sample_bonus = min(update.data_samples / 1000.0, 0.5)
        
        # Bonus za boljše performanse
        performance_bonus = 0.0
        if "accuracy" in update.performance_metrics:
            performance_bonus = update.performance_metrics["accuracy"] * 0.3
        
        return base_reward + sample_bonus + performance_bonus
    
    async def _trigger_aggregation(self) -> None:
        """Sproži agregacijo modelov"""
        try:
            if len(self.pending_updates) < self.min_nodes_for_aggregation:
                return
            
            start_time = time.time()
            
            # Izvedi agregacijo (FedAvg algoritem)
            aggregated_model = await self._federated_averaging()
            
            if aggregated_model:
                self.global_model = aggregated_model
                self.successful_aggregations += 1
                
                # Počisti čakalne posodobitve
                self.pending_updates.clear()
                
                # Logiraj uspešno agregacijo
                latency_ms = int((time.time() - start_time) * 1000)
                self.store.insert_event({
                    "agent_type": "federated_broker",
                    "task_type": "model_aggregation",
                    "success": True,
                    "reward": 2.0,  # Višja nagrada za uspešno agregacijo
                    "latency_ms": latency_ms,
                    "meta": {
                        "participating_nodes": len(aggregated_model.participating_nodes),
                        "model_version": aggregated_model.version,
                        "performance_metrics": aggregated_model.performance_metrics
                    }
                })
                
                # Posodobi policy manager z novimi metrikami
                await self._update_policy_from_aggregation(aggregated_model)
            
            self.total_rounds += 1
            
        except Exception as e:
            self.store.insert_event({
                "agent_type": "federated_broker",
                "task_type": "model_aggregation",
                "success": False,
                "reward": 0.0,
                "meta": {"error": str(e)}
            })
    
    async def _federated_averaging(self) -> Optional[GlobalModel]:
        """Implementira FedAvg algoritem za agregacijo modelov"""
        try:
            if not self.pending_updates:
                return None
            
            # Izračunaj uteženo povprečje gradientov
            total_samples = sum(update.data_samples for update in self.pending_updates)
            aggregated_gradients = {}
            
            for update in self.pending_updates:
                weight = update.data_samples / total_samples
                # Simulacija agregacije gradientov (v resničnem sistemu bi to bilo kompleksnejše)
                for key, value in update.performance_metrics.items():
                    if key not in aggregated_gradients:
                        aggregated_gradients[key] = 0.0
                    aggregated_gradients[key] += value * weight
            
            # Ustvari novo verzijo globalnega modela
            version = f"v{self.total_rounds + 1}_{int(time.time())}"
            model_hash = hashlib.md5(json.dumps(aggregated_gradients, sort_keys=True).encode()).hexdigest()
            
            participating_nodes = [update.node_id for update in self.pending_updates]
            
            return GlobalModel(
                version=version,
                model_hash=model_hash,
                aggregated_gradients=aggregated_gradients,
                participating_nodes=participating_nodes,
                performance_metrics=aggregated_gradients,
                created_at=time.time()
            )
            
        except Exception as e:
            print(f"Napaka pri agregaciji: {e}")
            return None
    
    async def _update_policy_from_aggregation(self, model: GlobalModel) -> None:
        """Posodobi policy manager z metrikami iz agregacije"""
        try:
            # Analiziraj performanse vozlišč
            node_performances = {}
            for update in self.pending_updates:
                if "accuracy" in update.performance_metrics:
                    node_performances[update.node_id] = update.performance_metrics["accuracy"]
            
            # Posodobi performanse vozlišč
            for node_id, performance in node_performances.items():
                if node_id in self.nodes:
                    self.nodes[node_id].performance_score = performance
            
            # Če imamo dovolj podatkov, posodobi prioritete providerjev
            if len(node_performances) >= 3:
                sorted_nodes = sorted(node_performances.items(), key=lambda x: x[1], reverse=True)
                top_nodes = [node_id for node_id, _ in sorted_nodes[:3]]
                
                # Simulacija posodobitve prioritet (v resničnem sistemu bi to bilo povezano s providerji)
                self.policy_manager.set_preferences(
                    provider_priority=["openai", "gemini", "vertex", "ollama"],  # Ohrani obstoječe
                    model_prefs={
                        "federated_learning": {
                            "openai": "gpt-4o",
                            "gemini": "gemini-1.5-pro"
                        }
                    }
                )
                
        except Exception as e:
            print(f"Napaka pri posodobitvi policy: {e}")
    
    async def get_global_model(self) -> Optional[GlobalModel]:
        """Vrne trenutni globalni model"""
        return self.global_model
    
    async def get_network_status(self) -> Dict[str, Any]:
        """Vrne status federativne mreže"""
        active_nodes = [node for node in self.nodes.values() if node.is_active]
        
        return {
            "node_id": self.node_id,
            "total_nodes": len(self.nodes),
            "active_nodes": len(active_nodes),
            "pending_updates": len(self.pending_updates),
            "total_rounds": self.total_rounds,
            "successful_aggregations": self.successful_aggregations,
            "success_rate": self.successful_aggregations / max(self.total_rounds, 1),
            "global_model_version": self.global_model.version if self.global_model else None,
            "last_aggregation": self.global_model.created_at if self.global_model else None
        }
    
    async def cleanup_inactive_nodes(self, timeout_seconds: int = 600) -> int:
        """Počisti neaktivna vozlišča"""
        current_time = time.time()
        removed_count = 0
        
        for node_id, node in list(self.nodes.items()):
            if current_time - node.last_seen > timeout_seconds:
                node.is_active = False
                removed_count += 1
                
                # Logiraj odstranitev
                self.store.insert_event({
                    "agent_type": "federated_broker",
                    "task_type": "node_cleanup",
                    "success": True,
                    "reward": 0.5,
                    "meta": {
                        "removed_node_id": node_id,
                        "inactive_duration": current_time - node.last_seen
                    }
                })
        
        return removed_count
    
    async def start_background_tasks(self) -> None:
        """Zažene ozadnje naloge za federativno učenje"""
        asyncio.create_task(self._periodic_aggregation())
        asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_aggregation(self) -> None:
        """Periodična agregacija modelov"""
        while True:
            try:
                await asyncio.sleep(self.aggregation_interval)
                if len(self.pending_updates) >= self.min_nodes_for_aggregation:
                    await self._trigger_aggregation()
            except Exception as e:
                print(f"Napaka pri periodični agregaciji: {e}")
    
    async def _periodic_cleanup(self) -> None:
        """Periodično čiščenje neaktivnih vozlišč"""
        while True:
            try:
                await asyncio.sleep(300)  # Vsakih 5 minut
                await self.cleanup_inactive_nodes()
            except Exception as e:
                print(f"Napaka pri periodičnem čiščenju: {e}")