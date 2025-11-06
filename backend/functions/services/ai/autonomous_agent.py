"""
Autonomous Agents Service

Self-improving AI agents with capabilities:
- Web search integration
- Self-healing error recovery
- Dynamic module generation
- Platform improvement recommendations
- Autonomous task execution
"""

import os
import logging
import json
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    """Agent execution states"""
    IDLE = "idle"
    THINKING = "thinking"
    SEARCHING = "searching"
    EXECUTING = "executing"
    HEALING = "healing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentAction:
    """Action taken by the agent"""
    action_type: str
    description: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AgentExecution:
    """Agent execution trace"""
    execution_id: str
    task: str
    state: AgentState
    actions: List[AgentAction] = field(default_factory=list)
    final_result: Optional[Any] = None
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    error_count: int = 0
    heal_count: int = 0


class AutonomousAgent:
    """
    Self-improving autonomous agent
    
    Capabilities:
    - Web search for real-time information
    - Self-healing when errors occur
    - Dynamic code/module generation
    - Platform improvement suggestions
    """
    
    def __init__(self, name: str = "OmniAgent"):
        self.name = name
        self.executions: Dict[str, AgentExecution] = {}
        self.knowledge_base: Dict[str, Any] = {}
        self.improvement_suggestions: List[Dict[str, Any]] = []
        
        # Initialize capabilities
        self._init_web_search()
        self._init_llm()
    
    def _init_web_search(self):
        """Initialize web search capability"""
        try:
            import httpx
            self.web_search_available = True
            self.httpx = httpx
        except ImportError:
            self.web_search_available = False
            logger.warning("Web search not available - httpx not installed")
    
    def _init_llm(self):
        """Initialize LLM for reasoning"""
        try:
            from services.ai.multi_llm_router import get_multi_llm_router
            self.llm_router = get_multi_llm_router()
            self.llm_available = True
        except Exception as e:
            self.llm_available = False
            logger.warning(f"LLM not available: {e}")
    
    async def execute_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        max_steps: int = 10
    ) -> AgentExecution:
        """
        Execute a task autonomously
        
        Args:
            task: Task description
            context: Additional context
            max_steps: Maximum execution steps
            
        Returns:
            Execution trace with results
        """
        execution_id = f"exec_{int(time.time())}_{len(self.executions)}"
        execution = AgentExecution(
            execution_id=execution_id,
            task=task,
            state=AgentState.THINKING
        )
        self.executions[execution_id] = execution
        
        logger.info(f"[{self.name}] Starting task: {task}")
        
        try:
            # Plan the task
            execution.state = AgentState.THINKING
            plan = await self._plan_task(task, context)
            
            action = AgentAction(
                action_type="plan",
                description="Created execution plan",
                parameters={"plan": plan}
            )
            execution.actions.append(action)
            
            # Execute steps
            for step_num, step in enumerate(plan.get("steps", []), 1):
                if step_num > max_steps:
                    logger.warning(f"Reached max steps ({max_steps})")
                    break
                
                logger.info(f"[{self.name}] Step {step_num}: {step['action']}")
                
                # Execute step with self-healing
                result = await self._execute_step_with_healing(
                    step, execution, context
                )
                
                if result.get("status") == "failed" and execution.error_count > 3:
                    execution.state = AgentState.FAILED
                    break
            
            # Generate final result
            execution.state = AgentState.COMPLETED
            execution.final_result = await self._synthesize_results(execution)
            
        except Exception as e:
            logger.error(f"[{self.name}] Task failed: {e}")
            execution.state = AgentState.FAILED
            execution.final_result = {"error": str(e)}
        
        execution.end_time = datetime.utcnow().isoformat()
        return execution
    
    async def _plan_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Plan task execution using LLM
        
        Args:
            task: Task description
            context: Additional context
            
        Returns:
            Execution plan with steps
        """
        if not self.llm_available:
            # Fallback plan
            return {
                "steps": [
                    {"action": "search", "query": task},
                    {"action": "synthesize", "topic": task}
                ]
            }
        
        planning_prompt = f"""You are an autonomous AI agent. Plan how to accomplish this task:

Task: {task}

Context: {json.dumps(context or {}, indent=2)}

Available capabilities:
- web_search: Search the web for information
- generate_code: Generate Python code
- analyze_platform: Analyze platform code and suggest improvements
- synthesize: Combine information to create an answer

Create a step-by-step plan as JSON with this format:
{{
    "steps": [
        {{"action": "action_name", "parameters": {{}}, "description": "what this does"}},
        ...
    ],
    "reasoning": "why this plan will work"
}}

Return ONLY the JSON, no other text."""
        
        try:
            response = await self.llm_router.complete(
                prompt=planning_prompt,
                strategy="BALANCED",
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse JSON from response
            content = response["content"]
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(content)
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            # Fallback plan
            return {
                "steps": [
                    {"action": "search", "query": task, "description": "Search for information"},
                    {"action": "synthesize", "topic": task, "description": "Create final answer"}
                ],
                "reasoning": "Fallback plan due to planning error"
            }
    
    async def _execute_step_with_healing(
        self,
        step: Dict[str, Any],
        execution: AgentExecution,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a step with self-healing on failure
        
        Args:
            step: Step to execute
            execution: Execution trace
            context: Context
            
        Returns:
            Step result
        """
        action = AgentAction(
            action_type=step.get("action", "unknown"),
            description=step.get("description", ""),
            parameters=step.get("parameters", {})
        )
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                execution.state = AgentState.EXECUTING
                
                # Execute based on action type
                if action.action_type == "web_search" or action.action_type == "search":
                    result = await self._web_search(
                        step.get("query") or step.get("parameters", {}).get("query") or context.get("query", "")
                    )
                elif action.action_type == "generate_code":
                    result = await self._generate_code(
                        step.get("requirements") or step.get("parameters", {}).get("requirements", "")
                    )
                elif action.action_type == "analyze_platform":
                    result = await self._analyze_platform(
                        step.get("parameters", {})
                    )
                elif action.action_type == "synthesize":
                    result = await self._synthesize_information(
                        step.get("topic") or step.get("parameters", {}).get("topic", ""),
                        execution
                    )
                else:
                    result = {"status": "skipped", "reason": f"Unknown action: {action.action_type}"}
                
                action.result = result
                execution.actions.append(action)
                return result
                
            except Exception as e:
                logger.error(f"Step failed (attempt {attempt + 1}): {e}")
                execution.error_count += 1
                action.error = str(e)
                
                if attempt < max_retries - 1:
                    # Try self-healing
                    execution.state = AgentState.HEALING
                    healing_result = await self._self_heal(step, e, execution)
                    execution.heal_count += 1
                    
                    if healing_result.get("healed"):
                        step = healing_result.get("modified_step", step)
                        continue
                
                # Final failure
                action.result = {"status": "failed", "error": str(e)}
                execution.actions.append(action)
                return action.result
    
    async def _web_search(self, query: str) -> Dict[str, Any]:
        """
        Search the web for information
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        if not self.web_search_available:
            return {
                "status": "unavailable",
                "message": "Web search not available"
            }
        
        try:
            # Use DuckDuckGo API (no key required)
            async with self.httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": "1"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract useful information
                    results = {
                        "query": query,
                        "abstract": data.get("Abstract", ""),
                        "abstract_url": data.get("AbstractURL", ""),
                        "related_topics": [
                            {"title": t.get("Text", ""), "url": t.get("FirstURL", "")}
                            for t in data.get("RelatedTopics", [])[:5]
                            if isinstance(t, dict) and "Text" in t
                        ]
                    }
                    
                    return {
                        "status": "success",
                        "results": results,
                        "source": "DuckDuckGo"
                    }
                
                return {"status": "error", "message": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _generate_code(self, requirements: str) -> Dict[str, Any]:
        """
        Generate code based on requirements
        
        Args:
            requirements: Code requirements
            
        Returns:
            Generated code
        """
        if not self.llm_available:
            return {
                "status": "unavailable",
                "message": "Code generation not available"
            }
        
        prompt = f"""Generate Python code for the following requirements:

{requirements}

Requirements:
- Include type hints
- Add docstrings
- Handle errors gracefully
- Follow PEP 8

Return ONLY the code, no explanations."""
        
        try:
            response = await self.llm_router.complete(
                prompt=prompt,
                strategy="QUALITY_OPTIMIZED",
                temperature=0.2,
                max_tokens=2000
            )
            
            code = response["content"]
            
            # Extract code from markdown if wrapped
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            return {
                "status": "success",
                "code": code,
                "requirements": requirements,
                "provider": response.get("provider")
            }
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _analyze_platform(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze platform and suggest improvements
        
        Args:
            parameters: Analysis parameters
            
        Returns:
            Analysis and suggestions
        """
        if not self.llm_available:
            return {
                "status": "unavailable",
                "message": "Platform analysis not available"
            }
        
        # Get platform statistics
        platform_info = {
            "total_routes": 37,  # Based on repository
            "total_services": 15,
            "active_features": [
                "Grafana Monitoring",
                "GDPR Compliance",
                "MFA Authentication",
                "Threat Detection",
                "RAG System",
                "Multi-LLM Router"
            ]
        }
        
        prompt = f"""Analyze this AI platform and suggest improvements:

Platform Information:
{json.dumps(platform_info, indent=2)}

Focus Areas:
- Performance optimizations
- Security enhancements
- New feature suggestions
- Architecture improvements
- Cost optimizations

Provide 5 specific, actionable recommendations as JSON:
{{
    "recommendations": [
        {{
            "title": "...",
            "category": "performance|security|features|architecture|cost",
            "priority": "high|medium|low",
            "description": "...",
            "implementation": "..."
        }}
    ]
}}

Return ONLY JSON."""
        
        try:
            response = await self.llm_router.complete(
                prompt=prompt,
                strategy="QUALITY_OPTIMIZED",
                temperature=0.5,
                max_tokens=2000
            )
            
            content = response["content"]
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(content)
            
            # Store suggestions
            for rec in analysis.get("recommendations", []):
                self.improvement_suggestions.append({
                    **rec,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "pending"
                })
            
            return {
                "status": "success",
                "analysis": analysis,
                "suggestions_added": len(analysis.get("recommendations", []))
            }
            
        except Exception as e:
            logger.error(f"Platform analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _synthesize_information(
        self,
        topic: str,
        execution: AgentExecution
    ) -> Dict[str, Any]:
        """
        Synthesize information from previous steps
        
        Args:
            topic: Topic to synthesize
            execution: Execution trace with context
            
        Returns:
            Synthesized result
        """
        if not self.llm_available:
            return {
                "status": "unavailable",
                "message": "Synthesis not available"
            }
        
        # Gather context from previous actions
        context_parts = []
        for action in execution.actions:
            if action.result and isinstance(action.result, dict):
                if action.result.get("status") == "success":
                    context_parts.append(f"{action.action_type}: {json.dumps(action.result, indent=2)}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""Based on the information gathered, provide a comprehensive answer about: {topic}

Information:
{context}

Provide a clear, well-structured response that synthesizes the information above."""
        
        try:
            response = await self.llm_router.complete(
                prompt=prompt,
                strategy="QUALITY_OPTIMIZED",
                temperature=0.7,
                max_tokens=1500
            )
            
            return {
                "status": "success",
                "synthesis": response["content"],
                "provider": response.get("provider")
            }
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _self_heal(
        self,
        failed_step: Dict[str, Any],
        error: Exception,
        execution: AgentExecution
    ) -> Dict[str, Any]:
        """
        Attempt to heal from an error
        
        Args:
            failed_step: The step that failed
            error: The error that occurred
            execution: Execution trace
            
        Returns:
            Healing result with modified step if successful
        """
        if not self.llm_available:
            return {"healed": False, "reason": "LLM not available for healing"}
        
        logger.info(f"[{self.name}] Attempting self-healing...")
        
        healing_prompt = f"""An autonomous agent encountered an error. Help fix it:

Failed Step:
{json.dumps(failed_step, indent=2)}

Error:
{str(error)}

Execution Context:
- Total errors: {execution.error_count}
- Previous actions: {len(execution.actions)}

Suggest a modified version of the step that might work, or an alternative approach.
Return JSON:
{{
    "can_heal": true/false,
    "modified_step": {{...}} or null,
    "reasoning": "why this should work"
}}

Return ONLY JSON."""
        
        try:
            response = await self.llm_router.complete(
                prompt=healing_prompt,
                strategy="QUALITY_OPTIMIZED",
                temperature=0.3,
                max_tokens=500
            )
            
            content = response["content"]
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            healing_result = json.loads(content)
            
            if healing_result.get("can_heal") and healing_result.get("modified_step"):
                logger.info(f"[{self.name}] Healing successful: {healing_result.get('reasoning')}")
                return {
                    "healed": True,
                    "modified_step": healing_result["modified_step"],
                    "reasoning": healing_result.get("reasoning")
                }
            
            return {"healed": False, "reason": "No healing strategy found"}
            
        except Exception as e:
            logger.error(f"Self-healing failed: {e}")
            return {"healed": False, "reason": str(e)}
    
    async def _synthesize_results(self, execution: AgentExecution) -> Dict[str, Any]:
        """
        Synthesize final results from execution
        
        Args:
            execution: Execution trace
            
        Returns:
            Final synthesized result
        """
        successful_actions = [
            action for action in execution.actions
            if action.result and isinstance(action.result, dict) and action.result.get("status") == "success"
        ]
        
        if not successful_actions:
            return {
                "status": "no_results",
                "message": "No successful actions completed"
            }
        
        # Find synthesis action if exists
        for action in reversed(execution.actions):
            if action.action_type == "synthesize" and action.result:
                return action.result
        
        # Otherwise, combine results
        combined = {
            "task": execution.task,
            "status": "completed",
            "actions_completed": len(successful_actions),
            "results": [action.result for action in successful_actions]
        }
        
        return combined
    
    def get_improvement_suggestions(
        self,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        status: str = "pending"
    ) -> List[Dict[str, Any]]:
        """
        Get platform improvement suggestions
        
        Args:
            category: Filter by category
            priority: Filter by priority
            status: Filter by status
            
        Returns:
            List of suggestions
        """
        suggestions = self.improvement_suggestions
        
        if category:
            suggestions = [s for s in suggestions if s.get("category") == category]
        if priority:
            suggestions = [s for s in suggestions if s.get("priority") == priority]
        if status:
            suggestions = [s for s in suggestions if s.get("status") == status]
        
        return suggestions
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        executions = sorted(
            self.executions.values(),
            key=lambda e: e.start_time,
            reverse=True
        )[:limit]
        
        return [
            {
                "execution_id": e.execution_id,
                "task": e.task,
                "state": e.state.value,
                "actions_count": len(e.actions),
                "error_count": e.error_count,
                "heal_count": e.heal_count,
                "start_time": e.start_time,
                "end_time": e.end_time
            }
            for e in executions
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        total_executions = len(self.executions)
        successful = sum(1 for e in self.executions.values() if e.state == AgentState.COMPLETED)
        failed = sum(1 for e in self.executions.values() if e.state == AgentState.FAILED)
        total_heals = sum(e.heal_count for e in self.executions.values())
        
        return {
            "agent_name": self.name,
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": round(successful / total_executions * 100, 1) if total_executions > 0 else 0,
            "total_self_heals": total_heals,
            "improvement_suggestions": len(self.improvement_suggestions),
            "pending_suggestions": len([s for s in self.improvement_suggestions if s.get("status") == "pending"]),
            "capabilities": {
                "web_search": self.web_search_available,
                "llm_reasoning": self.llm_available,
                "code_generation": self.llm_available,
                "self_healing": self.llm_available
            }
        }


# Singleton instance
_agent_instance: Optional[AutonomousAgent] = None


def get_autonomous_agent() -> AutonomousAgent:
    """Get or create the Autonomous Agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AutonomousAgent()
    return _agent_instance
