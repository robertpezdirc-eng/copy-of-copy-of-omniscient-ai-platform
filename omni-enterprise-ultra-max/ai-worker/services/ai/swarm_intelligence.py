"""
Swarm Intelligence Orchestrator
Ant Colony Optimization for platform-wide task distribution and optimization
"""

from typing import List, Dict, Any, Optional, Callable
import numpy as np
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


@dataclass
class Task:
    """Task representation"""
    task_id: str
    task_type: str
    priority: TaskPriority
    payload: Dict[str, Any]
    estimated_duration: float  # seconds
    dependencies: List[str] = None
    worker_affinity: Optional[str] = None


@dataclass
class Worker:
    """Worker agent representation"""
    worker_id: str
    capabilities: List[str]
    current_load: float = 0.0
    max_capacity: float = 1.0
    performance_history: List[float] = None
    
    def __post_init__(self):
        if self.performance_history is None:
            self.performance_history = []


class PheromoneTrail:
    """
    Pheromone trails for ant colony optimization
    Stronger pheromones = better paths
    """
    
    def __init__(self, evaporation_rate: float = 0.1):
        self.trails: Dict[str, float] = {}  # (task_type, worker_id) -> strength
        self.evaporation_rate = evaporation_rate
    
    def deposit(self, task_type: str, worker_id: str, quality: float):
        """
        Deposit pheromone on path
        
        Args:
            task_type: Type of task
            worker_id: Worker that executed task
            quality: Execution quality (0-1, higher = better)
        """
        key = f"{task_type}:{worker_id}"
        current = self.trails.get(key, 0.0)
        self.trails[key] = current + quality
    
    def evaporate(self):
        """Evaporate pheromones over time"""
        for key in self.trails:
            self.trails[key] *= (1 - self.evaporation_rate)
            if self.trails[key] < 0.01:
                self.trails[key] = 0.0
    
    def get_strength(self, task_type: str, worker_id: str) -> float:
        """Get pheromone strength for path"""
        key = f"{task_type}:{worker_id}"
        return self.trails.get(key, 0.0)
    
    def get_best_worker(self, task_type: str, available_workers: List[str]) -> Optional[str]:
        """
        Get worker with strongest pheromone trail
        
        Args:
            task_type: Type of task
            available_workers: List of worker IDs
        
        Returns:
            Best worker ID or None
        """
        if not available_workers:
            return None
        
        best_worker = None
        best_strength = -1
        
        for worker_id in available_workers:
            strength = self.get_strength(task_type, worker_id)
            if strength > best_strength:
                best_strength = strength
                best_worker = worker_id
        
        return best_worker


class SwarmOrchestrator:
    """
    Ant Colony Optimization orchestrator for task distribution
    
    Features:
    - Pheromone-based routing
    - Load balancing
    - Adaptive task assignment
    - Emergent optimization
    """
    
    def __init__(
        self,
        evaporation_rate: float = 0.1,
        exploration_rate: float = 0.2
    ):
        """
        Initialize swarm orchestrator
        
        Args:
            evaporation_rate: Pheromone decay rate
            exploration_rate: Probability of random exploration
        """
        self.pheromones = PheromoneTrail(evaporation_rate)
        self.exploration_rate = exploration_rate
        
        self.workers: Dict[str, Worker] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Dict[str, Any]] = []
        
        self.is_running = False
    
    def register_worker(self, worker: Worker):
        """
        Register a new worker agent
        
        Args:
            worker: Worker to register
        """
        self.workers[worker.worker_id] = worker
        logger.info(f"🐜 Worker registered: {worker.worker_id} (capabilities: {worker.capabilities})")
    
    def submit_task(self, task: Task):
        """
        Submit task to swarm
        
        Args:
            task: Task to execute
        """
        self.task_queue.append(task)
        logger.info(f"📋 Task submitted: {task.task_id} (priority: {task.priority.name})")
    
    async def assign_task(self, task: Task) -> Optional[str]:
        """
        Assign task to optimal worker using ACO
        
        Args:
            task: Task to assign
        
        Returns:
            Worker ID or None
        """
        # Find capable workers
        capable_workers = [
            w for w in self.workers.values()
            if task.task_type in w.capabilities
            and w.current_load < w.max_capacity
        ]
        
        if not capable_workers:
            return None
        
        # Check for worker affinity
        if task.worker_affinity and task.worker_affinity in self.workers:
            if task.worker_affinity in [w.worker_id for w in capable_workers]:
                return task.worker_affinity
        
        # Decide: exploit (pheromone) or explore (random)
        if np.random.random() < self.exploration_rate:
            # Exploration: random worker
            worker = np.random.choice(capable_workers)
            return worker.worker_id
        
        # Exploitation: pheromone-based selection
        worker_ids = [w.worker_id for w in capable_workers]
        
        # Calculate probabilities based on pheromones and load
        probabilities = []
        for worker in capable_workers:
            pheromone_strength = self.pheromones.get_strength(
                task.task_type,
                worker.worker_id
            )
            load_factor = 1.0 - worker.current_load  # Prefer less loaded
            
            # Combine pheromone and load
            score = (pheromone_strength + 0.1) * load_factor  # +0.1 to avoid zero
            probabilities.append(score)
        
        # Normalize probabilities
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]
        else:
            probabilities = [1.0 / len(probabilities)] * len(probabilities)
        
        # Select worker
        selected_worker = np.random.choice(capable_workers, p=probabilities)
        return selected_worker.worker_id
    
    async def execute_task(
        self,
        task: Task,
        worker_id: str,
        executor: Callable
    ) -> Dict[str, Any]:
        """
        Execute task on worker
        
        Args:
            task: Task to execute
            worker_id: Worker ID
            executor: Async function to execute task
        
        Returns:
            Execution result
        """
        worker = self.workers[worker_id]
        
        # Update worker load
        worker.current_load += task.estimated_duration / 10.0
        
        try:
            # Execute
            start_time = asyncio.get_event_loop().time()
            result = await executor(task.payload)
            end_time = asyncio.get_event_loop().time()
            
            actual_duration = end_time - start_time
            quality = min(1.0, task.estimated_duration / max(actual_duration, 0.1))
            
            # Deposit pheromone
            self.pheromones.deposit(task.task_type, worker_id, quality)
            
            # Update worker performance
            worker.performance_history.append(quality)
            if len(worker.performance_history) > 100:
                worker.performance_history = worker.performance_history[-100:]
            
            # Record completion
            self.completed_tasks.append({
                "task_id": task.task_id,
                "worker_id": worker_id,
                "duration": actual_duration,
                "quality": quality,
                "result": result
            })
            
            logger.info(f"✅ Task completed: {task.task_id} by {worker_id} (quality: {quality:.2f})")
            
            return {
                "status": "success",
                "task_id": task.task_id,
                "worker_id": worker_id,
                "duration": actual_duration,
                "quality": quality,
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Task execution failed: {task.task_id} - {e}")
            return {
                "status": "error",
                "task_id": task.task_id,
                "worker_id": worker_id,
                "error": str(e)
            }
        
        finally:
            # Release worker load
            worker.current_load = max(0, worker.current_load - task.estimated_duration / 10.0)
    
    async def process_queue(self, executor: Callable):
        """
        Process task queue continuously
        
        Args:
            executor: Async function to execute tasks
        """
        while self.is_running:
            if not self.task_queue:
                await asyncio.sleep(0.1)
                continue
            
            # Sort by priority
            self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
            
            # Process highest priority task
            task = self.task_queue.pop(0)
            
            # Assign to worker
            worker_id = await self.assign_task(task)
            
            if worker_id:
                # Execute in background
                asyncio.create_task(self.execute_task(task, worker_id, executor))
            else:
                # No capable worker, re-queue
                self.task_queue.append(task)
                await asyncio.sleep(1)
            
            # Evaporate pheromones
            self.pheromones.evaporate()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get swarm statistics
        
        Returns:
            Statistics dict
        """
        return {
            "n_workers": len(self.workers),
            "n_queued_tasks": len(self.task_queue),
            "n_completed_tasks": len(self.completed_tasks),
            "avg_quality": np.mean([t["quality"] for t in self.completed_tasks]) if self.completed_tasks else 0,
            "worker_loads": {
                w_id: w.current_load for w_id, w in self.workers.items()
            },
            "pheromone_trails": len(self.pheromones.trails)
        }


# Legacy compatibility
class SwarmIntelligenceOrchestrator:
    """Legacy orchestrator (simple version)"""
    def __init__(self):
        self.agents: List[Dict[str,Any]] = []

    async def register_agent(self, agent: Dict[str, Any]):
        self.agents.append(agent)

    async def coordinate(self, task: Dict[str, Any]) -> Dict[str, Any]:
        if not self.agents:
            return {"result": None, "confidence": 0.0, "steps": []}
        parts = [
            {"agent": a.get("name","agent"), "proposal": f"solution_part_{i+1}", "confidence": 0.7+0.05*i}
            for i,a in enumerate(self.agents[:3])
        ]
        conf = sum(p["confidence"] for p in parts)/len(parts)
        return {
            "task": task,
            "result": "combined_solution",
            "confidence": round(conf,2),
            "contributors": parts,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }


# Singleton orchestrator
_swarm_orchestrator = SwarmOrchestrator()


def get_swarm_orchestrator() -> SwarmOrchestrator:
    """Get singleton swarm orchestrator"""
    return _swarm_orchestrator
