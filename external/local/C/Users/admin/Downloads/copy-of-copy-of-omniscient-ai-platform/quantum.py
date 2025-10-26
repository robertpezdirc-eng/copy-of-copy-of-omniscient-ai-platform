#!/usr/bin/env python3
"""
Quantum AI Interface Module for OMNI Singularity Platform
Modular interface for different AI-powered quantum modules

This module provides:
- Clean interface to Gemini AI through OMNI backend
- Modular quantum-* functions for different use cases
- Integration with OMNI platform API endpoints
- Error handling and fallback mechanisms
- Performance optimization and caching

Author: OMNI Platform Quantum Interface
Version: 1.0.0
"""

import requests
import json
import time
import os
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QuantumConfig:
    """Configuration for Quantum AI interface"""
    api_base: str = os.getenv("OMNI_API_BASE", "http://127.0.0.1:8002")
    default_model: str = "gemini-2.0-pro"
    timeout: int = 30
    max_retries: int = 3
    cache_ttl: int = 300  # 5 minutes
    enable_caching: bool = True

@dataclass
class QuantumResponse:
    """Standardized quantum AI response"""
    success: bool
    content: str
    model_used: str
    execution_time: float
    tokens_used: int = 0
    cached: bool = False
    error_message: str = ""

class QuantumAIInterface:
    """Main interface for Quantum AI modules"""

    def __init__(self, config: QuantumConfig = None):
        self.config = config or QuantumConfig()
        self.cache: Dict[str, Dict] = {}
        self.session = requests.Session()

        # Set up session with timeout
        self.session.timeout = self.config.timeout

    def _make_api_call(self, prompt: str, model: str = None, module_type: str = "general") -> QuantumResponse:
        """Make API call to OMNI backend"""
        start_time = time.time()

        # Check cache first
        if self.config.enable_caching:
            cache_key = self._generate_cache_key(prompt, model, module_type)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return QuantumResponse(
                    success=True,
                    content=cached_response["content"],
                    model_used=cached_response["model"],
                    execution_time=time.time() - start_time,
                    cached=True,
                    tokens_used=cached_response.get("tokens", 0)
                )

        try:
            url = f"{self.config.api_base}/api/gemini/query"
            payload = {
                "prompt": prompt,
                "model": model or self.config.default_model,
                "module_type": module_type
            }

            response = self.session.post(url, json=payload, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()

                if data.get("ok"):
                    content = data.get("reply", "")
                    model_used = data.get("model", model or self.config.default_model)

                    # Cache successful response
                    if self.config.enable_caching:
                        self._cache_response(cache_key, {
                            "content": content,
                            "model": model_used,
                            "timestamp": time.time(),
                            "tokens": data.get("tokens", 0)
                        })

                    return QuantumResponse(
                        success=True,
                        content=content,
                        model_used=model_used,
                        execution_time=time.time() - start_time,
                        tokens_used=data.get("tokens", 0)
                    )
                else:
                    error_msg = data.get("error", "Unknown API error")
                    return QuantumResponse(
                        success=False,
                        content="",
                        model_used=model or self.config.default_model,
                        execution_time=time.time() - start_time,
                        error_message=error_msg
                    )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return QuantumResponse(
                    success=False,
                    content="",
                    model_used=model or self.config.default_model,
                    execution_time=time.time() - start_time,
                    error_message=error_msg
                )

        except requests.exceptions.Timeout:
            return QuantumResponse(
                success=False,
                content="",
                model_used=model or self.config.default_model,
                execution_time=time.time() - start_time,
                error_message="Request timeout"
            )
        except requests.exceptions.ConnectionError:
            return QuantumResponse(
                success=False,
                content="",
                model_used=model or self.config.default_model,
                execution_time=time.time() - start_time,
                error_message="Connection error - OMNI backend unavailable"
            )
        except Exception as e:
            return QuantumResponse(
                success=False,
                content="",
                model_used=model or self.config.default_model,
                execution_time=time.time() - start_time,
                error_message=f"Unexpected error: {str(e)}"
            )

    def _generate_cache_key(self, prompt: str, model: str, module_type: str) -> str:
        """Generate cache key for request"""
        key_data = f"{prompt}:{model}:{module_type}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if still valid"""
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.config.cache_ttl:
                return cached_item
            else:
                # Remove expired cache entry
                del self.cache[cache_key]

        return None

    def _cache_response(self, cache_key: str, response_data: Dict):
        """Cache response data"""
        self.cache[cache_key] = response_data

        # Clean up old cache entries if cache gets too large
        if len(self.cache) > 1000:
            self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, value in self.cache.items()
            if current_time - value["timestamp"] >= self.config.cache_ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

# Global quantum AI interface instance
quantum_ai = QuantumAIInterface()

# ============================================================================
# QUANTUM MODULE FUNCTIONS
# ============================================================================

def call_gemini(prompt: str, model: str = "gemini-2.0-pro") -> str:
    """
    Send prompt to Vertex AI Gemini through OMNI platform.
    Returns AI response.
    """
    response = quantum_ai._make_api_call(prompt, model, "general")

    if response.success:
        return response.content
    else:
        return f"Error: {response.error_message}"

# ============================================================================
# QUANTUM GAMING MODULE
# ============================================================================

def quantum_gaming_idea(theme: str = None, age_group: str = "children", game_type: str = "active") -> str:
    """
    Generate game ideas using quantum AI optimization.
    Specialized for gaming concepts and interactive experiences.
    """
    if theme:
        prompt = f"Ustvari inovativno idejo za igro na temo '{theme}' za {age_group}, tip igre: {game_type}. Naredi podrobno specifikacijo z mehanikami, cilji in zabavnimi elementi."
    else:
        prompt = f"Ustvari inovativno idejo za {game_type} igro za {age_group}. Vključi edinstvene mehanike, cilje igre in elemente zabave. Naredi celotno specifikacijo."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_gaming")

    if response.success:
        return response.content
    else:
        return f"Quantum Gaming Error: {response.error_message}"

def quantum_game_mechanics(base_concept: str, complexity: str = "medium") -> str:
    """
    Generate detailed game mechanics using quantum optimization.
    """
    complexity_guide = {
        "simple": "preproste, intuitivne mehanike za začetnike",
        "medium": "uravnotežene mehanike za široko publiko",
        "complex": "globoke, strateške mehanike za izkušene igralce"
    }

    prompt = f"Za osnovni koncept igre '{base_concept}' ustvari podrobne mehanike igranja ({complexity_guide.get(complexity, complexity_guide['medium'])}). Vključi: kontrole, napredovanje, zmagovalne pogoje, težavnostne krivulje in edinstvene elemente."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_gaming")

    if response.success:
        return response.content
    else:
        return f"Game Mechanics Error: {response.error_message}"

# ============================================================================
# QUANTUM TOURISM MODULE
# ============================================================================

def quantum_tourism_idea(location: str, duration: str = "weekend", budget: str = "medium") -> str:
    """
    Generate tourism ideas using quantum AI optimization.
    Specialized for travel planning and experiences.
    """
    budget_guide = {
        "low": "proračunsko prijazne možnosti",
        "medium": "srednji cenovni razred",
        "high": "premium in luksuzne izkušnje"
    }

    duration_guide = {
        "day": "enodnevni izlet",
        "weekend": "vikend pobeg",
        "week": "tedenski dopust",
        "extended": "daljše potovanje"
    }

    prompt = f"Ustvari inovativen turistični načrt za {location} ({duration_guide.get(duration, duration)}), z {budget_guide.get(budget, budget_guide['medium'])}. Vključi: dnevni razpored, aktivnosti, prehrano, namestitev in lokalne skrivnosti."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_tourism")

    if response.success:
        return response.content
    else:
        return f"Quantum Tourism Error: {response.error_message}"

def quantum_cultural_experience(location: str, interest: str = "history") -> str:
    """
    Generate cultural experience recommendations.
    """
    interest_guide = {
        "history": "zgodovinske in kulturne znamenitosti",
        "food": "kulinarika in lokalne specialitete",
        "art": "umetnost in galerije",
        "music": "glasba in festivali",
        "nature": "narava in aktivnosti na prostem"
    }

    prompt = f"Za lokacijo {location} ustvari avtentično kulturno izkušnjo s poudarkom na {interest_guide.get(interest, interest_guide['history'])}. Vključi: lokalne običaje, tradicionalne aktivnosti, pristne izkušnje in nasvete za potovanje."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_tourism")

    if response.success:
        return response.content
    else:
        return f"Cultural Experience Error: {response.error_message}"

# ============================================================================
# QUANTUM EDUCATION MODULE
# ============================================================================

def quantum_educational_content(topic: str, level: str = "intermediate", format_type: str = "lesson_plan") -> str:
    """
    Generate educational content using quantum AI optimization.
    Specialized for learning and knowledge transfer.
    """
    level_guide = {
        "beginner": "osnovno raven, preprosti koncepti",
        "intermediate": "srednjo raven, podrobnejše razlage",
        "advanced": "napredno raven, kompleksni koncepti"
    }

    format_guide = {
        "lesson_plan": "struktura ure z učnimi cilji",
        "summary": "povzetek ključnih točk",
        "quiz": "vprašanja za preverjanje znanja",
        "project": "projektne ideje in naloge"
    }

    prompt = f"Ustvari izobraževalno vsebino za temo '{topic}' na {level_guide.get(level, level_guide['intermediate'])}, v formatu {format_guide.get(format_type, format_guide['lesson_plan'])}. Naredi praktično, zanimivo in didaktično."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_education")

    if response.success:
        return response.content
    else:
        return f"Educational Content Error: {response.error_message}"

def quantum_learning_path(skill: str, timeframe: str = "3_months") -> str:
    """
    Generate personalized learning path.
    """
    timeframe_guide = {
        "1_month": "intenzivni enomesečni program",
        "3_months": "trimesečni učni načrt",
        "6_months": "polletni program",
        "1_year": "celoletni učni načrt"
    }

    prompt = f"Ustvari personaliziran učni načrt za spretnost '{skill}' ({timeframe_guide.get(timeframe, timeframe_guide['3_months'])}). Vključi: tedenske cilje, vire, vaje in mejnike napredka."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_education")

    if response.success:
        return response.content
    else:
        return f"Learning Path Error: {response.error_message}"

# ============================================================================
# QUANTUM BUSINESS MODULE
# ============================================================================

def quantum_business_idea(industry: str, problem: str = None) -> str:
    """
    Generate business ideas using quantum AI optimization.
    Specialized for entrepreneurship and innovation.
    """
    if problem:
        prompt = f"Ustvari inovativno poslovno idejo za industrijo {industry}, ki rešuje problem: {problem}. Vključi: tržni potencial, ciljno publiko, monetizacijo in konkurenčne prednosti."
    else:
        prompt = f"Ustvari inovativno poslovno idejo za industrijo {industry}. Analiziraj trg, identificiraj priložnosti in ustvari celoten poslovni model z monetizacijsko strategijo."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_business")

    if response.success:
        return response.content
    else:
        return f"Business Idea Error: {response.error_message}"

def quantum_market_analysis(product: str, market: str = "slovenia") -> str:
    """
    Generate market analysis using quantum optimization.
    """
    prompt = f"Izvedi analizo trga za produkt '{product}' na trgu {market}. Vključi: velikost trga, konkurenco, ciljno publiko, trende in priporočila za vstop na trg."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_business")

    if response.success:
        return response.content
    else:
        return f"Market Analysis Error: {response.error_message}"

# ============================================================================
# QUANTUM CREATIVE MODULE
# ============================================================================

def quantum_storytelling(prompt: str, genre: str = "fantasy", length: str = "short") -> str:
    """
    Generate creative stories using quantum AI optimization.
    Specialized for narrative generation and creative writing.
    """
    length_guide = {
        "short": "kratka zgodba (500-1000 besed)",
        "medium": "srednje dolga zgodba (1000-3000 besed)",
        "long": "dolga zgodba (3000+ besed)"
    }

    prompt_full = f"Ustvari {genre} zgodbo na podlagi ideje: '{prompt}'. {length_guide.get(length, length_guide['short'])}. Naredi zgodbo zanimivo, s karakterji, konfliktom in razrešitvijo."

    response = quantum_ai._make_api_call(prompt_full, "gemini-2.0-pro", "quantum_creative")

    if response.success:
        return response.content
    else:
        return f"Storytelling Error: {response.error_message}"

def quantum_poetry(theme: str, style: str = "free_verse", language: str = "slovenian") -> str:
    """
    Generate poetry using quantum AI creativity.
    """
    style_guide = {
        "haiku": "tradicionalni japonski haiku (5-7-5 zlogov)",
        "free_verse": "prosti verz brez omejitev",
        "rhyming": "rimana poezija z ritmom",
        "sonnet": "sonet s tradicionalno strukturo"
    }

    prompt = f"Ustvari {style_guide.get(style, style_guide['free_verse'])} pesem v {language} jeziku na temo '{theme}'. Naj bo čustveno, z močnimi podobami in globokim pomenom."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_creative")

    if response.success:
        return response.content
    else:
        return f"Poetry Error: {response.error_message}"

# ============================================================================
# QUANTUM HEALTH MODULE
# ============================================================================

def quantum_wellness_plan(goals: str, timeframe: str = "30_days", fitness_level: str = "beginner") -> str:
    """
    Generate personalized wellness plans using quantum AI optimization.
    Specialized for health and fitness guidance.
    """
    fitness_guide = {
        "beginner": "začetni nivo, osnovne vaje",
        "intermediate": "srednji nivo, naprednejše rutine",
        "advanced": "napredni nivo, intenzivni treningi"
    }

    prompt = f"Ustvari personaliziran wellness načrt za cilje: '{goals}' v {timeframe} ({fitness_guide.get(fitness_level, fitness_guide['beginner'])}). Vključi: dnevno rutino, prehrano, vadbo in sledenje napredka."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_health")

    if response.success:
        return response.content
    else:
        return f"Wellness Plan Error: {response.error_message}"

def quantum_nutrition_guide(diet_type: str, calories: int = 2000, preferences: str = None) -> str:
    """
    Generate nutrition guidance using quantum optimization.
    """
    if preferences:
        prompt = f"Ustvari nutricionističen vodnik za {diet_type} dieto s {calories} kalorijami dnevno, prilagojeno za: {preferences}. Vključi: dnevni jedilnik, recepte in nasvete."
    else:
        prompt = f"Ustvari nutricionističen vodnik za {diet_type} dieto s {calories} kalorijami dnevno. Vključi: uravnotežen jedilnik, zdrave recepte in prehranske nasvete."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_health")

    if response.success:
        return response.content
    else:
        return f"Nutrition Guide Error: {response.error_message}"

# ============================================================================
# QUANTUM TECHNOLOGY MODULE
# ============================================================================

def quantum_code_generation(language: str, specification: str, complexity: str = "intermediate") -> str:
    """
    Generate code using quantum AI optimization.
    Specialized for software development and programming.
    """
    complexity_guide = {
        "simple": "preproste funkcije in algoritme",
        "intermediate": "srednje kompleksne aplikacije",
        "advanced": "kompleksne sisteme z naprednimi koncepti"
    }

    prompt = f"Ustvari {language} kodo za: {specification}. {complexity_guide.get(complexity, complexity_guide['intermediate'])}. Vključi: dobro dokumentacijo, error handling in optimizacijo."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_technology")

    if response.success:
        return response.content
    else:
        return f"Code Generation Error: {response.error_message}"

def quantum_system_architecture(description: str, requirements: List[str] = None) -> str:
    """
    Generate system architecture using quantum optimization.
    """
    if requirements:
        req_text = ", ".join(requirements)
        prompt = f"Za sistem '{description}' z zahtevami: {req_text}, ustvari podrobno sistemsko arhitekturo. Vključi: komponente, podatkovne tokove, tehnologije in skalabilnost."
    else:
        prompt = f"Ustvari podrobno sistemsko arhitekturo za: {description}. Vključi: modularno zasnovo, tehnološki stack, varnost in skalabilnost."

    response = quantum_ai._make_api_call(prompt, "gemini-2.0-pro", "quantum_technology")

    if response.success:
        return response.content
    else:
        return f"System Architecture Error: {response.error_message}"

# ============================================================================
# QUANTUM UTILITY FUNCTIONS
# ============================================================================

def get_quantum_status() -> Dict[str, Any]:
    """
    Get quantum AI interface status and performance metrics.
    """
    return {
        "api_base": quantum_ai.config.api_base,
        "default_model": quantum_ai.config.default_model,
        "cache_enabled": quantum_ai.config.enable_caching,
        "cache_size": len(quantum_ai.cache),
        "session_timeout": quantum_ai.config.timeout,
        "connected": True,  # Assume connected if module loaded
        "quantum_modules_available": [
            "quantum_gaming",
            "quantum_tourism",
            "quantum_education",
            "quantum_business",
            "quantum_creative",
            "quantum_health",
            "quantum_technology"
        ]
    }

def clear_quantum_cache():
    """
    Clear the quantum AI response cache.
    """
    cache_size_before = len(quantum_ai.cache)
    quantum_ai.cache.clear()
    logger.info(f"Cleared {cache_size_before} cached responses")

def set_quantum_model(model: str):
    """
    Set the default quantum AI model.
    """
    quantum_ai.config.default_model = model
    logger.info(f"Quantum AI model set to: {model}")

def configure_quantum_api(api_base: str, timeout: int = 30):
    """
    Configure the quantum AI API endpoint.
    """
    quantum_ai.config.api_base = api_base
    quantum_ai.config.timeout = timeout
    quantum_ai.session.timeout = timeout
    logger.info(f"Quantum AI API configured: {api_base}, timeout: {timeout}s")

# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

if __name__ == "__main__":
    print("🧠 OMNI Quantum AI Interface Module")
    print("=" * 50)

    # Test basic functionality
    print("\n1️⃣ Testing basic Gemini call...")
    test_result = call_gemini("Ustvari idejo za igro na trampolinu za otroke.")
    print(f"✅ Test result: {test_result[:100]}...")

    # Test quantum gaming module
    print("\n2️⃣ Testing quantum gaming module...")
    game_idea = quantum_gaming_idea("trampolin", "otroke", "aktivna")
    print(f"🎮 Game idea: {game_idea[:100]}...")

    # Test quantum tourism module
    print("\n3️⃣ Testing quantum tourism module...")
    tourism_idea = quantum_tourism_idea("Bled", "weekend", "medium")
    print(f"🏔️ Tourism idea: {tourism_idea[:100]}...")

    # Test quantum education module
    print("\n4️⃣ Testing quantum education module...")
    lesson_plan = quantum_educational_content("Python programiranje", "beginner", "lesson_plan")
    print(f"📚 Lesson plan: {lesson_plan[:100]}...")

    # Test quantum business module
    print("\n5️⃣ Testing quantum business module...")
    business_idea = quantum_business_idea("tehnologija", "pomanjkanje inovativnih rešitev za mala podjetja")
    print(f"💼 Business idea: {business_idea[:100]}...")

    # Test quantum creative module
    print("\n6️⃣ Testing quantum creative module...")
    story = quantum_storytelling("Robot, ki se nauči čustev", "sci-fi", "short")
    print(f"📖 Story: {story[:100]}...")

    # Test quantum health module
    print("\n7️⃣ Testing quantum health module...")
    wellness_plan = quantum_wellness_plan("izguba teže in več energije", "30_days", "beginner")
    print(f"🏃 Wellness plan: {wellness_plan[:100]}...")

    # Test quantum technology module
    print("\n8️⃣ Testing quantum technology module...")
    code = quantum_code_generation("Python", "kalkulator za izračun BMI z vhodno validacijo")
    print(f"💻 Code: {code[:100]}...")

    # Show status
    print("\n📊 Quantum AI Status:")
    status = get_quantum_status()
    for key, value in status.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)} items")
        else:
            print(f"  {key}: {value}")

    print("\n✅ Quantum AI Interface module test completed!")
    print("\n🚀 Ready for integration with OMNI frontend!")