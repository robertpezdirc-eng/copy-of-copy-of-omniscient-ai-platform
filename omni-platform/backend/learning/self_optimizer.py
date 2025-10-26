from typing import Dict, Any, Optional

class SelfOptimizer:
    """
    Priporoča parametre (temperature, top_p, beam_size, max_tokens) glede na
    tip naloge in trend nagrad.
    Trenutno enostavna heuristika (lahko nadgradimo z RL metodo).
    """
    def recommend(self, task_type: Optional[str], success_rate: float, avg_latency_ms: float) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        # temperature
        if task_type == "creative":
            params["temperature"] = 0.9 if success_rate >= 0.6 else 0.7
            params["top_p"] = 0.95
        elif task_type == "factual":
            params["temperature"] = 0.2 if success_rate >= 0.7 else 0.1
            params["top_p"] = 0.7
        elif task_type == "code":
            params["temperature"] = 0.1
            params["top_p"] = 0.6
        else:
            params["temperature"] = 0.5
            params["top_p"] = 0.9
        # beam_size (za modele, ki podpirajo)
        params["beam_size"] = 1 if avg_latency_ms > 1000 else 3
        # max_tokens
        params["max_tokens"] = 1024 if task_type == "creative" else 512
        return params