import os
import time
import json
import asyncio
import random
import numpy as np
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from .feedback_store import FeedbackStore
from .policy_manager import PolicyManager
from .federated_broker import FederatedLearningBroker, ModelSnapshot
from ..adapters.ipfs_storage_adapter import IPFSStorageAdapter

@dataclass
class LearningScenario:
    """Scenarij za testiranje in učenje"""
    scenario_id: str
    name: str
    description: str
    test_prompts: List[str]
    expected_outcomes: Dict[str, Any]
    complexity_level: str  # "simple", "medium", "complex"
    modalities: List[str]
    success_criteria: Dict[str, float]

@dataclass
class ExperimentResult:
    """Rezultat eksperimenta"""
    scenario_id: str
    provider: str
    model: str
    success_rate: float
    avg_latency: float
    avg_reward: float
    timestamp: float
    sample_size: int

@dataclass
class OptimizationState:
    """Stanje optimizacije"""
    current_round: int
    total_experiments: int
    successful_optimizations: int
    last_improvement: float
    best_configuration: Dict[str, Any]
    learning_rate: float
    exploration_rate: float

class ContinuousLearningEngine:
    """
    Neprekinjeni učni motor, ki aktivno optimizira politike med mirovanjem.
    Agent se nikoli ne ustavi in vedno išče izboljšave.
    """
    
    def __init__(self,
                 store: Optional[FeedbackStore] = None,
                 policy_manager: Optional[PolicyManager] = None,
                 federated_broker: Optional[FederatedLearningBroker] = None,
                 ipfs_adapter: Optional[IPFSStorageAdapter] = None):
        
        self.store = store or FeedbackStore()
        self.policy_manager = policy_manager or PolicyManager(self.store)
        self.federated_broker = federated_broker
        self.ipfs_adapter = ipfs_adapter
        
        # Stanje učenja
        self.is_running = False
        self.optimization_state = OptimizationState(
            current_round=0,
            total_experiments=0,
            successful_optimizations=0,
            last_improvement=time.time(),
            best_configuration={},
            learning_rate=float(os.getenv("LEARNING_RATE", "0.1")),
            exploration_rate=float(os.getenv("EXPLORATION_RATE", "0.3"))
        )
        
        # Konfiguracija
        self.idle_threshold = int(os.getenv("IDLE_THRESHOLD_SECONDS", "60"))
        self.experiment_interval = int(os.getenv("EXPERIMENT_INTERVAL", "300"))  # 5 min
        self.max_concurrent_experiments = int(os.getenv("MAX_CONCURRENT_EXPERIMENTS", "3"))
        self.scenario_rotation_interval = int(os.getenv("SCENARIO_ROTATION", "1800"))  # 30 min
        
        # Scenariji za testiranje
        self.learning_scenarios = self._initialize_scenarios()
        self.current_scenario_index = 0
        
        # Metrike
        self.last_user_activity = time.time()
        self.experiment_queue: List[LearningScenario] = []
        self.running_experiments: Dict[str, asyncio.Task] = {}
        
    def _initialize_scenarios(self) -> List[LearningScenario]:
        """Inicializira scenarije za učenje"""
        return [
            LearningScenario(
                scenario_id="text_generation_simple",
                name="Enostavna generacija besedila",
                description="Testiranje osnovnih sposobnosti generiranja besedila",
                test_prompts=[
                    "Napiši kratek povzetek o umetni inteligenci.",
                    "Razloži, kaj je strojno učenje.",
                    "Opiši prednosti oblačnih storitev."
                ],
                expected_outcomes={"min_length": 50, "max_length": 200},
                complexity_level="simple",
                modalities=["text"],
                success_criteria={"min_coherence": 0.7, "max_latency_ms": 5000}
            ),
            LearningScenario(
                scenario_id="code_generation",
                name="Generiranje kode",
                description="Testiranje sposobnosti generiranja in razlage kode",
                test_prompts=[
                    "Napiši Python funkcijo za sortiranje seznama.",
                    "Ustvari REST API endpoint v FastAPI.",
                    "Razloži, kako deluje rekurzija."
                ],
                expected_outcomes={"contains_code": True, "syntax_valid": True},
                complexity_level="complex",
                modalities=["text", "code"],
                success_criteria={"min_accuracy": 0.8, "max_latency_ms": 10000}
            ),
            LearningScenario(
                scenario_id="multimodal_analysis",
                name="Multimodalna analiza",
                description="Testiranje sposobnosti analize različnih modalnosti",
                test_prompts=[
                    "Analiziraj sliko in opiši, kaj vidiš.",
                    "Prepiši zvočni posnetek v besedilo.",
                    "Kombiniraj vizualne in tekstualne informacije."
                ],
                expected_outcomes={"modality_integration": True},
                complexity_level="complex",
                modalities=["text", "image", "audio"],
                success_criteria={"min_integration_score": 0.75, "max_latency_ms": 15000}
            ),
            LearningScenario(
                scenario_id="reasoning_logic",
                name="Logično sklepanje",
                description="Testiranje sposobnosti logičnega sklepanja",
                test_prompts=[
                    "Reši matematični problem: 2x + 5 = 15",
                    "Če je A > B in B > C, kaj lahko sklepamo o A in C?",
                    "Analiziraj vzročno-posledične povezave v scenariju."
                ],
                expected_outcomes={"logical_consistency": True, "correct_reasoning": True},
                complexity_level="medium",
                modalities=["text", "logic"],
                success_criteria={"min_accuracy": 0.85, "max_latency_ms": 8000}
            ),
            LearningScenario(
                scenario_id="creative_tasks",
                name="Kreativne naloge",
                description="Testiranje kreativnih sposobnosti",
                test_prompts=[
                    "Napiši kratko zgodbo o robotih.",
                    "Ustvari seznam inovativnih idej za aplikacijo.",
                    "Sestavi pesem o naravi."
                ],
                expected_outcomes={"creativity_score": 0.7, "originality": True},
                complexity_level="medium",
                modalities=["text", "creative"],
                success_criteria={"min_creativity": 0.6, "max_latency_ms": 12000}
            )
        ]
    
    async def start_continuous_learning(self) -> None:
        """Zažene neprekinjeno učenje"""
        if self.is_running:
            return
        
        self.is_running = True
        print("🧠 Neprekinjeni učni motor zagnan - agent je vedno aktiven!")
        
        # Zaženi ozadnje naloge
        tasks = [
            asyncio.create_task(self._activity_monitor()),
            asyncio.create_task(self._experiment_scheduler()),
            asyncio.create_task(self._optimization_loop()),
            asyncio.create_task(self._scenario_rotator()),
            asyncio.create_task(self._performance_analyzer()),
            asyncio.create_task(self._model_persistence_manager())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"Napaka v neprekinjenim učenju: {e}")
            self.is_running = False
    
    async def stop_continuous_learning(self) -> None:
        """Ustavi neprekinjeno učenje"""
        self.is_running = False
        
        # Ustavi tekoče eksperimente
        for task in self.running_experiments.values():
            task.cancel()
        
        self.running_experiments.clear()
        print("🛑 Neprekinjeni učni motor ustavljen")
    
    def mark_user_activity(self) -> None:
        """Označi aktivnost uporabnika"""
        self.last_user_activity = time.time()
    
    def is_system_idle(self) -> bool:
        """Preveri, ali je sistem v mirovanju"""
        return time.time() - self.last_user_activity > self.idle_threshold
    
    async def _activity_monitor(self) -> None:
        """Spremlja aktivnost sistema"""
        while self.is_running:
            try:
                # Preveri aktivnost iz feedback store
                recent_events = self.store.recent_events(limit=10)
                if recent_events:
                    latest_event = max(recent_events, key=lambda x: x["ts"])
                    if time.time() - latest_event["ts"] < self.idle_threshold:
                        self.mark_user_activity()
                
                await asyncio.sleep(30)  # Preveri vsakih 30 sekund
                
            except Exception as e:
                print(f"Napaka pri spremljanju aktivnosti: {e}")
                await asyncio.sleep(60)
    
    async def _experiment_scheduler(self) -> None:
        """Razporeja eksperimente med mirovanjem"""
        while self.is_running:
            try:
                if self.is_system_idle() and len(self.running_experiments) < self.max_concurrent_experiments:
                    # Izberi scenarij za testiranje
                    scenario = self._select_next_scenario()
                    if scenario:
                        # Zaženi eksperiment
                        experiment_id = f"exp_{int(time.time())}_{scenario.scenario_id}"
                        task = asyncio.create_task(self._run_experiment(scenario, experiment_id))
                        self.running_experiments[experiment_id] = task
                        
                        print(f"🔬 Zaganjam eksperiment: {scenario.name}")
                
                await asyncio.sleep(self.experiment_interval)
                
            except Exception as e:
                print(f"Napaka pri razporejanju eksperimentov: {e}")
                await asyncio.sleep(60)
    
    def _select_next_scenario(self) -> Optional[LearningScenario]:
        """Izbere naslednji scenarij za testiranje"""
        if not self.learning_scenarios:
            return None
        
        # Uporabi epsilon-greedy strategijo
        if random.random() < self.optimization_state.exploration_rate:
            # Raziskovanje - naključni scenarij
            return random.choice(self.learning_scenarios)
        else:
            # Izkoriščanje - najboljši scenarij
            scenario_scores = self._calculate_scenario_scores()
            if scenario_scores:
                best_scenario_id = max(scenario_scores, key=scenario_scores.get)
                return next((s for s in self.learning_scenarios if s.scenario_id == best_scenario_id), None)
            else:
                return self.learning_scenarios[self.current_scenario_index]
    
    def _calculate_scenario_scores(self) -> Dict[str, float]:
        """Izračuna ocene scenarijev na podlagi zgodovine"""
        scores = {}
        
        # Analiziraj nedavne dogodke
        recent_events = self.store.recent_events(limit=1000)
        
        for scenario in self.learning_scenarios:
            scenario_events = [
                e for e in recent_events 
                if e.get("meta", {}).get("scenario_id") == scenario.scenario_id
            ]
            
            if scenario_events:
                avg_reward = sum(e["reward"] for e in scenario_events) / len(scenario_events)
                success_rate = sum(1 for e in scenario_events if e["success"]) / len(scenario_events)
                scores[scenario.scenario_id] = avg_reward * success_rate
            else:
                scores[scenario.scenario_id] = 0.5  # Nevtralna ocena za nepreizkušene scenarije
        
        return scores
    
    async def _run_experiment(self, scenario: LearningScenario, experiment_id: str) -> ExperimentResult:
        """Izvede eksperiment s scenarijem"""
        try:
            start_time = time.time()
            results = []
            
            # Testiraj različne kombinacije provider/model
            providers_models = [
                ("openai", "gpt-4o-mini"),
                ("openai", "gpt-4o"),
                ("gemini", "gemini-1.5-flash"),
                ("gemini", "gemini-1.5-pro")
            ]
            
            for provider, model in providers_models:
                if not self.is_system_idle():
                    break  # Prekini, če sistem ni več v mirovanju
                
                # Testiraj z naključnim promptom iz scenarija
                prompt = random.choice(scenario.test_prompts)
                
                # Simuliraj izvajanje (v resničnem sistemu bi to klicalo dejanske API-je)
                latency_ms, success, reward = await self._simulate_api_call(
                    provider, model, prompt, scenario
                )
                
                # Zabeleži rezultat
                self.store.insert_event({
                    "agent_type": "continuous_learning",
                    "provider": provider,
                    "model": model,
                    "task_type": scenario.scenario_id,
                    "success": success,
                    "reward": reward,
                    "latency_ms": latency_ms,
                    "meta": {
                        "experiment_id": experiment_id,
                        "scenario_id": scenario.scenario_id,
                        "prompt_length": len(prompt),
                        "complexity": scenario.complexity_level
                    }
                })
                
                results.append({
                    "provider": provider,
                    "model": model,
                    "success": success,
                    "reward": reward,
                    "latency_ms": latency_ms
                })
                
                # Kratka pavza med klici
                await asyncio.sleep(1)
            
            # Analiziraj rezultate
            if results:
                best_result = max(results, key=lambda x: x["reward"])
                
                experiment_result = ExperimentResult(
                    scenario_id=scenario.scenario_id,
                    provider=best_result["provider"],
                    model=best_result["model"],
                    success_rate=sum(1 for r in results if r["success"]) / len(results),
                    avg_latency=sum(r["latency_ms"] for r in results) / len(results),
                    avg_reward=sum(r["reward"] for r in results) / len(results),
                    timestamp=time.time(),
                    sample_size=len(results)
                )
                
                # Posodobi optimizacijsko stanje
                await self._update_optimization_state(experiment_result)
                
                return experiment_result
            
        except Exception as e:
            print(f"Napaka pri eksperimentu {experiment_id}: {e}")
        
        finally:
            # Počisti iz seznama tekočih eksperimentov
            if experiment_id in self.running_experiments:
                del self.running_experiments[experiment_id]
            
            self.optimization_state.total_experiments += 1
    
    async def _simulate_api_call(self, provider: str, model: str, prompt: str, scenario: LearningScenario) -> Tuple[int, bool, float]:
        """Simulira API klic (v resničnem sistemu bi to klicalo dejanske API-je)"""
        # Simulacija latence
        base_latency = {
            "openai": {"gpt-4o-mini": 2000, "gpt-4o": 4000},
            "gemini": {"gemini-1.5-flash": 1500, "gemini-1.5-pro": 3500}
        }
        
        latency = base_latency.get(provider, {}).get(model, 3000)
        latency += random.randint(-500, 1000)  # Dodaj naključnost
        
        # Simulacija uspešnosti
        success_rates = {
            "simple": 0.95,
            "medium": 0.85,
            "complex": 0.75
        }
        
        success_rate = success_rates.get(scenario.complexity_level, 0.8)
        success = random.random() < success_rate
        
        # Izračunaj nagrado
        reward = 1.0 if success else 0.0
        
        # Bonus za hitrost
        if latency < scenario.success_criteria.get("max_latency_ms", 10000):
            reward += 0.2
        
        # Bonus za kompleksnost
        complexity_bonus = {"simple": 0.1, "medium": 0.2, "complex": 0.3}
        reward += complexity_bonus.get(scenario.complexity_level, 0.0)
        
        # Simuliraj čas izvajanja
        await asyncio.sleep(latency / 1000.0)
        
        return latency, success, reward
    
    async def _update_optimization_state(self, result: ExperimentResult) -> None:
        """Posodobi stanje optimizacije"""
        try:
            # Preveri, ali je to izboljšava
            current_best = self.optimization_state.best_configuration.get(result.scenario_id, {})
            current_best_reward = current_best.get("avg_reward", 0.0)
            
            if result.avg_reward > current_best_reward:
                self.optimization_state.best_configuration[result.scenario_id] = {
                    "provider": result.provider,
                    "model": result.model,
                    "avg_reward": result.avg_reward,
                    "success_rate": result.success_rate,
                    "timestamp": result.timestamp
                }
                
                self.optimization_state.successful_optimizations += 1
                self.optimization_state.last_improvement = time.time()
                
                print(f"✨ Izboljšava najdena za {result.scenario_id}: {result.provider}/{result.model} (nagrada: {result.avg_reward:.3f})")
                
                # Posodobi policy manager
                await self._apply_optimization(result)
            
            # Prilagodi exploration rate
            self._adjust_exploration_rate()
            
        except Exception as e:
            print(f"Napaka pri posodobitvi optimizacije: {e}")
    
    async def _apply_optimization(self, result: ExperimentResult) -> None:
        """Uporabi optimizacijo v policy managerju"""
        try:
            # Posodobi preference za ta tip naloge
            current_prefs = self.policy_manager.store.get_policy_state().get("model_prefs", {})
            
            if result.scenario_id not in current_prefs:
                current_prefs[result.scenario_id] = {}
            
            current_prefs[result.scenario_id][result.provider] = result.model
            
            # Posodobi policy manager
            self.policy_manager.set_preferences(model_prefs=current_prefs)
            
            # Če imamo federated broker, shrani model snapshot
            if self.federated_broker and self.ipfs_adapter:
                snapshot = ModelSnapshot(
                    model_id=f"optimized_{result.scenario_id}",
                    version=f"v{self.optimization_state.current_round}",
                    model_data={
                        "provider": result.provider,
                        "model": result.model,
                        "optimization_round": self.optimization_state.current_round
                    },
                    training_metadata={
                        "scenario_id": result.scenario_id,
                        "experiment_count": self.optimization_state.total_experiments,
                        "learning_rate": self.optimization_state.learning_rate
                    },
                    performance_metrics={
                        "avg_reward": result.avg_reward,
                        "success_rate": result.success_rate,
                        "avg_latency": result.avg_latency
                    }
                )
                
                await self.ipfs_adapter.store_model_snapshot(snapshot)
            
        except Exception as e:
            print(f"Napaka pri uporabi optimizacije: {e}")
    
    def _adjust_exploration_rate(self) -> None:
        """Prilagodi stopnjo raziskovanja"""
        # Zmanjšaj exploration rate, če imamo nedavne izboljšave
        time_since_improvement = time.time() - self.optimization_state.last_improvement
        
        if time_since_improvement < 3600:  # Manj kot 1 ura
            self.optimization_state.exploration_rate = max(0.1, self.optimization_state.exploration_rate * 0.95)
        else:
            self.optimization_state.exploration_rate = min(0.5, self.optimization_state.exploration_rate * 1.05)
    
    async def _optimization_loop(self) -> None:
        """Glavna optimizacijska zanka"""
        while self.is_running:
            try:
                self.optimization_state.current_round += 1
                
                # Analiziraj performanse
                await self._analyze_performance_trends()
                
                # Prilagodi strategijo učenja
                await self._adapt_learning_strategy()
                
                await asyncio.sleep(1800)  # Vsakih 30 minut
                
            except Exception as e:
                print(f"Napaka v optimizacijski zanki: {e}")
                await asyncio.sleep(300)
    
    async def _scenario_rotator(self) -> None:
        """Rotira scenarije za raznolikost"""
        while self.is_running:
            try:
                self.current_scenario_index = (self.current_scenario_index + 1) % len(self.learning_scenarios)
                await asyncio.sleep(self.scenario_rotation_interval)
                
            except Exception as e:
                print(f"Napaka pri rotaciji scenarijev: {e}")
                await asyncio.sleep(300)
    
    async def _performance_analyzer(self) -> None:
        """Analizira performanse in išče vzorce"""
        while self.is_running:
            try:
                # Analiziraj nedavne dogodke
                recent_events = self.store.recent_events(limit=500)
                
                if len(recent_events) >= 100:
                    # Analiziraj trende
                    await self._detect_performance_patterns(recent_events)
                
                await asyncio.sleep(900)  # Vsakih 15 minut
                
            except Exception as e:
                print(f"Napaka pri analizi performans: {e}")
                await asyncio.sleep(300)
    
    async def _model_persistence_manager(self) -> None:
        """Upravlja persistenco modelov"""
        while self.is_running:
            try:
                if self.ipfs_adapter:
                    # Shrani trenutno stanje optimizacije
                    state_data = asdict(self.optimization_state)
                    state_data["scenarios"] = [asdict(s) for s in self.learning_scenarios]
                    
                    await self.ipfs_adapter.add_json(
                        state_data,
                        f"optimization_state_{int(time.time())}.json",
                        {"type": "optimization_state", "round": self.optimization_state.current_round}
                    )
                
                await asyncio.sleep(3600)  # Vsako uro
                
            except Exception as e:
                print(f"Napaka pri persistenci modelov: {e}")
                await asyncio.sleep(600)
    
    async def _analyze_performance_trends(self) -> None:
        """Analizira trende performans"""
        try:
            summary_by_provider = self.store.summary_by_provider()
            
            if summary_by_provider:
                print("📊 Analiza trendov performans:")
                for provider_data in summary_by_provider[:3]:
                    print(f"  {provider_data['provider']}: {provider_data['avg_reward']:.3f} avg reward, {provider_data['success']} uspehov")
            
        except Exception as e:
            print(f"Napaka pri analizi trendov: {e}")
    
    async def _adapt_learning_strategy(self) -> None:
        """Prilagodi strategijo učenja"""
        try:
            # Prilagodi learning rate glede na uspešnost
            success_rate = self.optimization_state.successful_optimizations / max(self.optimization_state.total_experiments, 1)
            
            if success_rate > 0.3:
                self.optimization_state.learning_rate = min(0.3, self.optimization_state.learning_rate * 1.1)
            else:
                self.optimization_state.learning_rate = max(0.01, self.optimization_state.learning_rate * 0.9)
            
        except Exception as e:
            print(f"Napaka pri prilagajanju strategije: {e}")
    
    async def _detect_performance_patterns(self, events: List[Dict[str, Any]]) -> None:
        """Zazna vzorce v performansah"""
        try:
            # Analiziraj vzorce po času dneva
            hourly_performance = {}
            
            for event in events:
                hour = datetime.fromtimestamp(event["ts"]).hour
                if hour not in hourly_performance:
                    hourly_performance[hour] = []
                hourly_performance[hour].append(event["reward"])
            
            # Najdi najboljše ure
            best_hours = []
            for hour, rewards in hourly_performance.items():
                if len(rewards) >= 5:  # Dovolj vzorcev
                    avg_reward = sum(rewards) / len(rewards)
                    if avg_reward > 0.8:
                        best_hours.append(hour)
            
            if best_hours:
                print(f"🕐 Najboljše ure za performanse: {best_hours}")
            
        except Exception as e:
            print(f"Napaka pri zaznavanju vzorcev: {e}")
    
    async def get_learning_status(self) -> Dict[str, Any]:
        """Vrne status neprekinjnega učenja"""
        return {
            "is_running": self.is_running,
            "system_idle": self.is_system_idle(),
            "optimization_state": asdict(self.optimization_state),
            "running_experiments": len(self.running_experiments),
            "total_scenarios": len(self.learning_scenarios),
            "last_user_activity": self.last_user_activity,
            "uptime_hours": (time.time() - self.last_user_activity) / 3600 if self.is_running else 0
        }