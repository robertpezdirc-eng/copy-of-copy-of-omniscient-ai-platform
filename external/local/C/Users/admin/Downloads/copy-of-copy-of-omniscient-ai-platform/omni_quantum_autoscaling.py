#!/usr/bin/env python3
"""
OMNI Quantum Auto-Scaling and Load Balancing System
Dynamic Resource Management for Quantum Computing Infrastructure

Features:
- Auto-scaling quantum processing cores based on demand
- Intelligent load balancing across quantum nodes
- Dynamic resource allocation and deallocation
- Predictive scaling based on workload patterns
- Real-time performance monitoring and adjustment
- Cost optimization for quantum computing resources
- Fault tolerance and automatic recovery
"""

import asyncio
import json
import time
import psutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class ScalingPolicy(Enum):
    """Auto-scaling policies"""
    CONSERVATIVE = "conservative"  # Scale up slowly, scale down quickly
    AGGRESSIVE = "aggressive"      # Scale up quickly, scale down slowly
    BALANCED = "balanced"          # Moderate scaling in both directions
    PREDICTIVE = "predictive"      # Use ML to predict scaling needs

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RESPONSE_TIME = "weighted_response_time"
    QUANTUM_AWARE = "quantum_aware"
    ADAPTIVE = "adaptive"

@dataclass
class ScalingMetrics:
    """Metrics for auto-scaling decisions"""
    timestamp: float
    current_load: float
    average_load: float
    peak_load: float
    cores_active: int
    cores_available: int
    queue_length: int
    response_time: float
    memory_usage: float
    cpu_usage: float

@dataclass
class ScalingDecision:
    """Auto-scaling decision"""
    decision_id: str
    timestamp: float
    action: str  # "scale_up", "scale_down", "no_action"
    cores_to_add: int
    cores_to_remove: int
    reason: str
    confidence: float
    estimated_impact: Dict[str, float]

class QuantumAutoScaler:
    """Auto-scaling system for quantum computing resources"""

    def __init__(self, min_cores: int = 2, max_cores: int = 32):
        self.min_cores = min_cores
        self.max_cores = max_cores
        self.scaling_policy = ScalingPolicy.BALANCED
        self.current_cores = min_cores

        # Scaling parameters
        self.scale_up_threshold = 0.8   # Scale up when load > 80%
        self.scale_down_threshold = 0.3  # Scale down when load < 30%
        self.scale_evaluation_interval = 30  # Evaluate every 30 seconds
        self.cooldown_period = 60       # Cooldown between scaling actions

        # Metrics and history
        self.scaling_metrics = []
        self.scaling_history = []
        self.last_scaling_action = 0

        # Monitoring
        self.monitoring_thread = None
        self.is_monitoring = False

    def start_auto_scaling(self, core_manager) -> bool:
        """Start auto-scaling system"""
        try:
            self.core_manager = core_manager
            self.is_monitoring = True

            # Start monitoring thread
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()

            print(f"🚀 Auto-scaling started: {self.min_cores}-{self.max_cores} cores")
            return True

        except Exception as e:
            print(f"❌ Failed to start auto-scaling: {e}")
            return False

    def stop_auto_scaling(self):
        """Stop auto-scaling system"""
        self.is_monitoring = False

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        print("🛑 Auto-scaling stopped")

    def _monitoring_loop(self):
        """Main monitoring and scaling loop"""
        while self.is_monitoring:
            try:
                # Collect current metrics
                metrics = self._collect_scaling_metrics()

                if metrics:
                    self.scaling_metrics.append(metrics)

                    # Keep only recent metrics (last hour)
                    cutoff_time = time.time() - 3600
                    self.scaling_metrics = [m for m in self.scaling_metrics if m.timestamp > cutoff_time]

                    # Evaluate scaling needs
                    scaling_decision = self._evaluate_scaling_needs(metrics)

                    if scaling_decision:
                        self._execute_scaling_decision(scaling_decision)

                # Wait for next evaluation
                time.sleep(self.scale_evaluation_interval)

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(self.scale_evaluation_interval)

    def _collect_scaling_metrics(self) -> Optional[ScalingMetrics]:
        """Collect current scaling metrics"""
        try:
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100.0

            # Get quantum core metrics
            if hasattr(self.core_manager, 'get_cluster_metrics'):
                cluster_metrics = self.core_manager.get_cluster_metrics()
                current_load = cluster_metrics.get('average_workload', 0.0)
                cores_active = cluster_metrics.get('active_cores', 0)
                cores_available = cluster_metrics.get('total_cores', 0)
            else:
                current_load = 0.5  # Default if no metrics available
                cores_active = self.current_cores
                cores_available = self.current_cores

            # Calculate additional metrics
            average_load = np.mean([m.current_load for m in self.scaling_metrics[-10:]]) if self.scaling_metrics else current_load
            peak_load = max([m.current_load for m in self.scaling_metrics[-10:]]) if self.scaling_metrics else current_load

            # Estimate queue length and response time
            queue_length = max(0, int(current_load * 10))  # Simple estimation
            response_time = max(0.1, current_load * 2)    # Simple estimation

            return ScalingMetrics(
                timestamp=time.time(),
                current_load=current_load,
                average_load=average_load,
                peak_load=peak_load,
                cores_active=cores_active,
                cores_available=cores_available,
                queue_length=queue_length,
                response_time=response_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage
            )

        except Exception as e:
            print(f"Error collecting metrics: {e}")
            return None

    def _evaluate_scaling_needs(self, metrics: ScalingMetrics) -> Optional[ScalingDecision]:
        """Evaluate if scaling is needed"""
        current_time = time.time()

        # Check cooldown period
        if current_time - self.last_scaling_action < self.cooldown_period:
            return None

        # Apply scaling policy
        if self.scaling_policy == ScalingPolicy.CONSERVATIVE:
            scale_up_threshold = 0.9
            scale_down_threshold = 0.2
        elif self.scaling_policy == ScalingPolicy.AGGRESSIVE:
            scale_up_threshold = 0.7
            scale_down_threshold = 0.4
        elif self.scaling_policy == ScalingPolicy.PREDICTIVE:
            return self._predictive_scaling_evaluation(metrics)
        else:  # BALANCED
            scale_up_threshold = self.scale_up_threshold
            scale_down_threshold = self.scale_down_threshold

        # Evaluate scaling needs
        if metrics.current_load > scale_up_threshold and self.current_cores < self.max_cores:
            # Scale up
            cores_to_add = self._calculate_scale_up_amount(metrics)
            confidence = min(1.0, metrics.current_load)

            return ScalingDecision(
                decision_id=f"scale_up_{int(current_time)}",
                timestamp=current_time,
                action="scale_up",
                cores_to_add=cores_to_add,
                cores_to_remove=0,
                reason=f"High load: {metrics.current_load:.2f} > {scale_up_threshold}",
                confidence=confidence,
                estimated_impact=self._estimate_scaling_impact("scale_up", cores_to_add, metrics)
            )

        elif metrics.current_load < scale_down_threshold and self.current_cores > self.min_cores:
            # Scale down
            cores_to_remove = self._calculate_scale_down_amount(metrics)
            confidence = min(1.0, 1.0 - metrics.current_load)

            return ScalingDecision(
                decision_id=f"scale_down_{int(current_time)}",
                timestamp=current_time,
                action="scale_down",
                cores_to_add=0,
                cores_to_remove=cores_to_remove,
                reason=f"Low load: {metrics.current_load:.2f} < {scale_down_threshold}",
                confidence=confidence,
                estimated_impact=self._estimate_scaling_impact("scale_down", -cores_to_remove, metrics)
            )

        # No scaling needed
        return ScalingDecision(
            decision_id=f"no_action_{int(current_time)}",
            timestamp=current_time,
            action="no_action",
            cores_to_add=0,
            cores_to_remove=0,
            reason="Load within acceptable range",
            confidence=1.0,
            estimated_impact={}
        )

    def _predictive_scaling_evaluation(self, metrics: ScalingMetrics) -> Optional[ScalingDecision]:
        """Predictive scaling using trend analysis"""
        if len(self.scaling_metrics) < 10:
            # Not enough data for prediction
            return self._evaluate_scaling_needs_balanced(metrics)

        # Analyze load trend
        recent_metrics = self.scaling_metrics[-10:]
        load_trend = self._calculate_load_trend(recent_metrics)

        # Predict future load
        predicted_load = metrics.current_load + load_trend * 5  # Predict 5 steps ahead

        # Make scaling decision based on prediction
        if predicted_load > 0.85 and self.current_cores < self.max_cores:
            return ScalingDecision(
                decision_id=f"predictive_scale_up_{int(time.time())}",
                timestamp=time.time(),
                action="scale_up",
                cores_to_add=1,
                cores_to_remove=0,
                reason=f"Predicted high load: {predicted_load:.2f}",
                confidence=0.8,
                estimated_impact={"predicted_load": predicted_load}
            )

        elif predicted_load < 0.2 and self.current_cores > self.min_cores:
            return ScalingDecision(
                decision_id=f"predictive_scale_down_{int(time.time())}",
                timestamp=time.time(),
                action="scale_down",
                cores_to_add=0,
                cores_to_remove=1,
                reason=f"Predicted low load: {predicted_load:.2f}",
                confidence=0.7,
                estimated_impact={"predicted_load": predicted_load}
            )

        return None

    def _calculate_load_trend(self, metrics: List[ScalingMetrics]) -> float:
        """Calculate load trend from recent metrics"""
        if len(metrics) < 2:
            return 0.0

        # Simple linear trend
        loads = [m.current_load for m in metrics]
        time_points = [m.timestamp for m in metrics]

        # Calculate slope
        if len(set(time_points)) == 1:
            return 0.0

        slope = np.polyfit(time_points, loads, 1)[0]
        return slope

    def _calculate_scale_up_amount(self, metrics: ScalingMetrics) -> int:
        """Calculate how many cores to add"""
        load_excess = metrics.current_load - self.scale_up_threshold
        cores_to_add = max(1, int(load_excess * 5))  # Scale based on load excess

        # Cap at maximum allowed
        max_add = self.max_cores - self.current_cores
        return min(cores_to_add, max_add)

    def _calculate_scale_down_amount(self, metrics: ScalingMetrics) -> int:
        """Calculate how many cores to remove"""
        load_deficit = self.scale_down_threshold - metrics.current_load
        cores_to_remove = max(1, int(load_deficit * 3))  # Scale based on load deficit

        # Cap at minimum needed
        max_remove = self.current_cores - self.min_cores
        return min(cores_to_remove, max_remove)

    def _estimate_scaling_impact(self, action: str, core_change: int, metrics: ScalingMetrics) -> Dict[str, float]:
        """Estimate impact of scaling decision"""
        impact = {}

        if action == "scale_up":
            new_core_count = self.current_cores + core_change
            impact["new_core_count"] = new_core_count
            impact["estimated_load_reduction"] = metrics.current_load / new_core_count * self.current_cores
            impact["estimated_response_time_improvement"] = metrics.response_time * 0.7  # 30% improvement
            impact["estimated_cost_increase"] = core_change * 0.1  # Cost per additional core

        elif action == "scale_down":
            new_core_count = max(self.min_cores, self.current_cores + core_change)
            impact["new_core_count"] = new_core_count
            impact["estimated_load_increase"] = metrics.current_load / new_core_count * self.current_cores
            impact["estimated_cost_savings"] = abs(core_change) * 0.1  # Savings per removed core

        return impact

    def _execute_scaling_decision(self, decision: ScalingDecision):
        """Execute scaling decision"""
        try:
            if decision.action == "scale_up" and decision.cores_to_add > 0:
                self._scale_up_cores(decision.cores_to_add)
            elif decision.action == "scale_down" and decision.cores_to_remove > 0:
                self._scale_down_cores(decision.cores_to_remove)

            # Record decision
            self.scaling_history.append(decision)
            self.last_scaling_action = time.time()

            print(f"⚖️ Scaling {decision.action}: {decision.reason}")

        except Exception as e:
            print(f"Error executing scaling decision: {e}")

    def _scale_up_cores(self, cores_to_add: int):
        """Scale up quantum cores"""
        try:
            # Add cores to core manager
            if hasattr(self.core_manager, 'add_cores'):
                self.core_manager.add_cores(cores_to_add)
            else:
                # Simulate core addition
                print(f"  Adding {cores_to_add} quantum cores")

            self.current_cores += cores_to_add
            print(f"  ✅ Scaled up to {self.current_cores} cores")

        except Exception as e:
            print(f"Error scaling up cores: {e}")

    def _scale_down_cores(self, cores_to_remove: int):
        """Scale down quantum cores"""
        try:
            # Remove cores from core manager
            if hasattr(self.core_manager, 'remove_cores'):
                self.core_manager.remove_cores(cores_to_remove)
            else:
                # Simulate core removal
                print(f"  Removing {cores_to_remove} quantum cores")

            self.current_cores -= cores_to_remove
            print(f"  ✅ Scaled down to {self.current_cores} cores")

        except Exception as e:
            print(f"Error scaling down cores: {e}")

    def get_scaling_status(self) -> Dict[str, Any]:
        """Get current auto-scaling status"""
        if not self.scaling_metrics:
            return {"status": "no_metrics"}

        latest_metrics = self.scaling_metrics[-1]

        return {
            "current_cores": self.current_cores,
            "min_cores": self.min_cores,
            "max_cores": self.max_cores,
            "scaling_policy": self.scaling_policy.value,
            "current_load": latest_metrics.current_load,
            "average_load": latest_metrics.average_load,
            "last_scaling_action": self.last_scaling_action,
            "scaling_history_count": len(self.scaling_history),
            "is_monitoring": self.is_monitoring,
            "next_evaluation_in": max(0, self.scale_evaluation_interval - (time.time() - (self.scaling_metrics[-1].timestamp if self.scaling_metrics else 0)))
        }

class QuantumLoadBalancer:
    """Advanced load balancer for quantum computing resources"""

    def __init__(self):
        self.balancing_strategy = LoadBalancingStrategy.ADAPTIVE
        self.core_weights = {}
        self.request_queue = []
        self.balancing_history = []

        # Load balancing parameters
        self.rebalance_interval = 15  # Rebalance every 15 seconds
        self.performance_window = 60  # Consider last 60 seconds for performance

    def distribute_quantum_tasks(self, tasks: List[Dict], available_cores: List) -> List[Dict]:
        """Distribute tasks across quantum cores using selected strategy"""
        if not tasks or not available_cores:
            return []

        if self.balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_distribution(tasks, available_cores)
        elif self.balancing_strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_distribution(tasks, available_cores)
        elif self.balancing_strategy == LoadBalancingStrategy.WEIGHTED_RESPONSE_TIME:
            return self._weighted_response_time_distribution(tasks, available_cores)
        elif self.balancing_strategy == LoadBalancingStrategy.QUANTUM_AWARE:
            return self._quantum_aware_distribution(tasks, available_cores)
        else:  # ADAPTIVE
            return self._adaptive_distribution(tasks, available_cores)

    def _round_robin_distribution(self, tasks: List[Dict], cores: List) -> List[Dict]:
        """Simple round-robin distribution"""
        distributed_tasks = []

        for i, task in enumerate(tasks):
            core = cores[i % len(cores)]
            distributed_tasks.append({
                "task": task,
                "assigned_core": core,
                "assignment_time": time.time(),
                "strategy": "round_robin"
            })

        return distributed_tasks

    def _least_connections_distribution(self, tasks: List[Dict], cores: List) -> List[Dict]:
        """Distribute to cores with least active connections"""
        distributed_tasks = []

        # Count current connections per core
        core_connections = {core: 0 for core in cores}

        for task in tasks:
            # Find core with least connections
            best_core = min(core_connections.items(), key=lambda x: x[1])[0]

            distributed_tasks.append({
                "task": task,
                "assigned_core": best_core,
                "assignment_time": time.time(),
                "strategy": "least_connections"
            })

            core_connections[best_core] += 1

        return distributed_tasks

    def _weighted_response_time_distribution(self, tasks: List[Dict], cores: List) -> List[Dict]:
        """Distribute based on weighted response time"""
        distributed_tasks = []

        # Calculate weights based on recent performance
        core_weights = self._calculate_response_time_weights(cores)

        for task in tasks:
            # Select core using weighted probability
            weights = [core_weights.get(core, 1.0) for core in cores]
            total_weight = sum(weights)

            if total_weight == 0:
                # Fallback to round-robin
                core = cores[len(distributed_tasks) % len(cores)]
            else:
                # Weighted selection
                probabilities = [w / total_weight for w in weights]
                core_idx = np.random.choice(len(cores), p=probabilities)
                core = cores[core_idx]

            distributed_tasks.append({
                "task": task,
                "assigned_core": core,
                "assignment_time": time.time(),
                "strategy": "weighted_response_time",
                "core_weight": core_weights.get(core, 1.0)
            })

        return distributed_tasks

    def _quantum_aware_distribution(self, tasks: List[Dict], cores: List) -> List[Dict]:
        """Quantum-aware distribution considering qubit requirements"""
        distributed_tasks = []

        for task in tasks:
            task_qubits = task.get('qubits', 10)

            # Find core that can best handle this task's quantum requirements
            best_core = None
            best_score = float('-inf')

            for core in cores:
                # Calculate suitability score
                core_qubits = core.hardware_specs.get('qubits', 10)
                core_workload = core.current_workload

                # Prefer cores with sufficient qubits
                if core_qubits < task_qubits:
                    continue

                # Score based on capability and current load
                capability_score = core_qubits - task_qubits
                load_penalty = core_workload * 2

                score = capability_score - load_penalty

                if score > best_score:
                    best_score = score
                    best_core = core

            if best_core is None:
                # Fallback to least loaded core
                best_core = min(cores, key=lambda c: c.current_workload)

            distributed_tasks.append({
                "task": task,
                "assigned_core": best_core,
                "assignment_time": time.time(),
                "strategy": "quantum_aware",
                "task_qubits": task_qubits,
                "core_qubits": best_core.hardware_specs.get('qubits', 10)
            })

        return distributed_tasks

    def _adaptive_distribution(self, tasks: List[Dict], cores: List) -> List[Dict]:
        """Adaptive distribution that adjusts strategy based on conditions"""
        # Analyze current conditions
        total_load = sum(core.current_workload for core in cores)
        avg_load = total_load / len(cores) if cores else 0

        # Choose strategy based on load conditions
        if avg_load > 0.8:
            # High load - use quantum-aware for optimal distribution
            return self._quantum_aware_distribution(tasks, cores)
        elif avg_load < 0.3:
            # Low load - use round-robin for simplicity
            return self._round_robin_distribution(tasks, cores)
        else:
            # Medium load - use weighted response time
            return self._weighted_response_time_distribution(tasks, cores)

    def _calculate_response_time_weights(self, cores: List) -> Dict:
        """Calculate weights based on recent response times"""
        weights = {}

        for core in cores:
            # Get recent performance metrics
            if hasattr(core, 'performance_metrics'):
                recent_time = core.performance_metrics.get('last_execution_time', 1.0)
                # Lower response time = higher weight
                weights[core] = 1.0 / max(recent_time, 0.1)
            else:
                weights[core] = 1.0  # Default weight

        return weights

    def update_core_weights(self, core_performance: Dict):
        """Update core weights based on performance"""
        for core_id, performance in core_performance.items():
            self.core_weights[core_id] = performance.get('weight', 1.0)

    def get_load_balancing_report(self) -> Dict[str, Any]:
        """Get comprehensive load balancing report"""
        return {
            "balancing_strategy": self.balancing_strategy.value,
            "rebalance_interval": self.rebalance_interval,
            "core_weights": self.core_weights,
            "balancing_history_length": len(self.balancing_history),
            "queue_length": len(self.request_queue)
        }

class QuantumResourceManager:
    """Integrated resource manager for quantum computing"""

    def __init__(self):
        self.auto_scaler = QuantumAutoScaler()
        self.load_balancer = QuantumLoadBalancer()

        # Resource pools
        self.cpu_pool = []
        self.gpu_pool = []
        self.memory_pool = []

        # Resource allocation tracking
        self.allocation_history = []

    def initialize_resource_management(self, core_manager) -> bool:
        """Initialize resource management system"""
        try:
            # Initialize resource pools
            self._initialize_resource_pools()

            # Start auto-scaling
            if not self.auto_scaler.start_auto_scaling(core_manager):
                return False

            print("✅ Quantum resource management initialized")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize resource management: {e}")
            return False

    def _initialize_resource_pools(self):
        """Initialize resource pools"""
        # CPU pool
        cpu_count = multiprocessing.cpu_count()
        self.cpu_pool = [f"cpu_core_{i}" for i in range(cpu_count)]

        # GPU pool (if available)
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            self.gpu_pool = [f"gpu_{gpu.id}" for gpu in gpus]
        except:
            self.gpu_pool = []

        # Memory pool
        memory_gb = psutil.virtual_memory().total // (1024**3)
        self.memory_pool = [f"memory_block_{i}" for i in range(memory_gb)]

        print(f"📊 Resource pools: {len(self.cpu_pool)} CPU, {len(self.gpu_pool)} GPU, {len(self.memory_pool)} GB memory")

    def allocate_resources_for_task(self, task: Dict) -> Dict[str, Any]:
        """Allocate resources for a quantum computing task"""
        start_time = time.time()

        # Determine resource requirements
        requirements = self._analyze_task_requirements(task)

        # Allocate from pools
        allocation = {
            "cpu_cores": min(requirements['cpu_cores'], len(self.cpu_pool)),
            "gpu_units": min(requirements['gpu_units'], len(self.gpu_pool)),
            "memory_gb": min(requirements['memory_gb'], len(self.memory_pool))
        }

        # Track allocation
        self.allocation_history.append({
            "task_id": task.get('id', 'unknown'),
            "allocation": allocation,
            "timestamp": time.time(),
            "allocation_time": time.time() - start_time
        })

        return {
            "success": True,
            "allocation": allocation,
            "allocation_time": time.time() - start_time,
            "resource_utilization": self._calculate_resource_utilization()
        }

    def _analyze_task_requirements(self, task: Dict) -> Dict[str, int]:
        """Analyze resource requirements for a task"""
        # Base requirements
        base_cpu = 1
        base_gpu = 0
        base_memory = 2  # GB

        # Adjust based on task complexity
        complexity = task.get('complexity', 0.5)
        qubits = task.get('qubits', 10)

        # Scale requirements based on complexity and qubits
        cpu_cores = max(1, int(base_cpu * complexity * np.sqrt(qubits / 10)))
        gpu_units = 1 if qubits > 15 and complexity > 0.7 else 0
        memory_gb = max(2, int(base_memory * complexity * (qubits / 10)))

        return {
            "cpu_cores": cpu_cores,
            "gpu_units": gpu_units,
            "memory_gb": memory_gb
        }

    def _calculate_resource_utilization(self) -> Dict[str, float]:
        """Calculate current resource utilization"""
        total_allocations = len(self.allocation_history)

        if total_allocations == 0:
            return {"cpu": 0.0, "gpu": 0.0, "memory": 0.0}

        # Calculate utilization from recent allocations
        recent_allocations = self.allocation_history[-100:]  # Last 100 allocations

        avg_cpu = np.mean([a['allocation']['cpu_cores'] for a in recent_allocations])
        avg_gpu = np.mean([a['allocation']['gpu_units'] for a in recent_allocations])
        avg_memory = np.mean([a['allocation']['memory_gb'] for a in recent_allocations])

        return {
            "cpu": min(1.0, avg_cpu / len(self.cpu_pool)),
            "gpu": min(1.0, avg_gpu / len(self.gpu_pool)) if self.gpu_pool else 0.0,
            "memory": min(1.0, avg_memory / len(self.memory_pool))
        }

    def get_resource_management_report(self) -> Dict[str, Any]:
        """Get comprehensive resource management report"""
        return {
            "auto_scaler_status": self.auto_scaler.get_scaling_status(),
            "load_balancer_report": self.load_balancer.get_load_balancing_report(),
            "resource_pools": {
                "cpu_cores": len(self.cpu_pool),
                "gpu_units": len(self.gpu_pool),
                "memory_gb": len(self.memory_pool)
            },
            "current_utilization": self._calculate_resource_utilization(),
            "allocation_history_count": len(self.allocation_history)
        }

# Global resource manager
quantum_resource_manager = QuantumResourceManager()

def initialize_quantum_resource_management(core_manager) -> bool:
    """Initialize quantum resource management system"""
    return quantum_resource_manager.initialize_resource_management(core_manager)

def get_quantum_resource_status() -> Dict[str, Any]:
    """Get current quantum resource status"""
    return quantum_resource_manager.get_resource_management_report()

if __name__ == "__main__":
    # Example usage
    print("🚀 OMNI Quantum Auto-Scaling and Load Balancing System")
    print("=" * 70)

    # Initialize resource management (without core manager for demo)
    print("🔧 Initializing resource management...")

    # Simulate resource pools
    quantum_resource_manager._initialize_resource_pools()

    # Test task allocation
    test_tasks = [
        {"id": "task1", "qubits": 5, "complexity": 0.3},
        {"id": "task2", "qubits": 15, "complexity": 0.8},
        {"id": "task3", "qubits": 8, "complexity": 0.5}
    ]

    print(f"\n📋 Testing resource allocation for {len(test_tasks)} tasks...")

    for task in test_tasks:
        allocation = quantum_resource_manager.allocate_resources_for_task(task)
        print(f"  Task {task['id']}: {allocation['allocation']} (CPU: {allocation['allocation']['cpu_cores']}, "
              f"GPU: {allocation['allocation']['gpu_units']}, Memory: {allocation['allocation']['memory_gb']}GB)")

    # Get resource status
    status = get_quantum_resource_status()
    print("
📊 Resource Status:"    print(f"  CPU Pool: {status['resource_pools']['cpu_cores']} cores")
    print(f"  GPU Pool: {status['resource_pools']['gpu_units']} units")
    print(f"  Memory Pool: {status['resource_pools']['memory_gb']} GB")
    print(f"  CPU Utilization: {status['current_utilization']['cpu']:.2f}")
    print(f"  GPU Utilization: {status['current_utilization']['gpu']:.2f}")
    print(f"  Memory Utilization: {status['current_utilization']['memory']:.2f}")

    print("\n✅ Quantum auto-scaling and load balancing test completed!")