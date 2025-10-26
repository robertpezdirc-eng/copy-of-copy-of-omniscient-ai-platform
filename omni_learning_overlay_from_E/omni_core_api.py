#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# OMNI Learning Overlay - Core API Connector
Povezava z obstoječim OMNI Core sistemom
"""

import requests
import json
import time
from typing import List, Dict, Any

class OmniCoreAPI:
    """Povezava z obstoječim OMNI Core sistemom"""

    def __init__(self, base_url="http://localhost:3001/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 10

    def get_all_agents(self) -> List[str]:
        """Pridobi seznam vseh aktivnih agentov iz Core-a"""
        try:
            response = self.session.get(
                f"{self.base_url}/agents/status",
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                # Pridobi agente iz odgovora
                agents = []

                # Če so agenti v agents polju
                if 'agents' in data:
                    agents = list(data['agents'].keys())
                elif 'active_agents' in data:
                    agents = data['active_agents']
                else:
                    # Fallback na privzete agente
                    agents = ["learning", "commercial", "optimization"]

                print(f"🔗 Povezan z OMNI Core - agenti: {agents}")
                return agents
            else:
                print(f"⚠️ OMNI Core vrnil status {response.status_code}")
                return ["learning", "commercial", "optimization"]

        except requests.exceptions.RequestException as e:
            print(f"❌ Napaka pri povezavi z OMNI Core: {e}")
            return ["learning", "commercial", "optimization"]
        except Exception as e:
            print(f"❌ Nepričakovana napaka: {e}")
            return ["learning", "commercial", "optimization"]

    def ask_agent_ai(self, agent_id: str, message: str) -> str:
        """Vprašaj določenega agenta preko OMNI Core API-ja"""
        try:
            response = self.session.post(
                f"{self.base_url}/chat",
                json={
                    'message': message,
                    'userId': f'overlay_{agent_id}',
                    'aiProvider': 'auto'
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('response', 'Odgovor prejet.')
                else:
                    return f"Napaka: {data.get('error', 'Neznana napaka')}"
            else:
                return f"HTTP napaka {response.status_code}: {response.text}"

        except requests.exceptions.RequestException as e:
            return f"Napaka pri povezavi: {e}"
        except Exception as e:
            return f"Nepričakovana napaka: {e}"

    def learn_agent_ai(self, agent_id: str, topic: str) -> str:
        """Agenta nauči novo temo preko OMNI Core-a"""
        learning_prompt = f"""
        Kot {agent_id} agent se učim novo temo: {topic}.
        Analiziraj to temo in podaj 3 ključne točke ki sem se jih naučil.
        Če nisi prepričan o odgovoru, povej da potrebuješ več informacij.
        Odgovori v slovenščini.
        """

        return self.ask_agent_ai(agent_id, learning_prompt)

    def get_system_status(self) -> Dict[str, Any]:
        """Pridobi trenutni status sistema"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def test_connectivity(self) -> bool:
        """Testiraj povezljivost z OMNI Core"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

# Globalna instanca za enostavno uporabo
omni_core = OmniCoreAPI()

# API funkcije za zunanjo uporabo
def get_all_agents() -> List[str]:
    """API funkcija za pridobitev vseh agentov"""
    return omni_core.get_all_agents()

def ask_agent_ai(agent_id: str, message: str) -> str:
    """API funkcija za vprašanje agenta"""
    return omni_core.ask_agent_ai(agent_id, message)

def learn_agent_ai(agent_id: str, topic: str) -> str:
    """API funkcija za učenje agenta"""
    return omni_core.learn_agent_ai(agent_id, topic)

def get_system_status() -> Dict[str, Any]:
    """API funkcija za status sistema"""
    return omni_core.get_system_status()

def test_connectivity() -> bool:
    """API funkcija za test povezljivosti"""
    return omni_core.test_connectivity()

if __name__ == "__main__":
    # Test povezljivosti
    print("🔗 Testiranje OMNI Core povezljivosti...")

    if test_connectivity():
        print("✅ OMNI Core je dosegljiv")

        # Test 1: Pridobi agente
        print("\n🤖 Test 1: Pridobivanje agentov")
        agents = get_all_agents()
        print(f"Agenti: {agents}")

        # Test 2: Vprašaj agenta
        print("\n💬 Test 2: Vprašanje agenta")
        if agents:
            response = ask_agent_ai(agents[0], "Kako se imaš danes?")
            print(f"Odgovor: {response[:100]}...")

        # Test 3: Učenje agenta
        print("\n📚 Test 3: Učenje agenta")
        if agents:
            learned = learn_agent_ai(agents[0], "testna tema")
            print(f"Naučeno: {learned[:100]}...")

    else:
        print("❌ OMNI Core ni dosegljiv")
        print("🔧 Rešitve:")
        print("   1. Prepričajte se da OMNI server teče na portu 3001")
        print("   2. Preverite požarni zid nastavitve")
        print("   3. Preverite omrežno povezljivost")

    print("\n✅ Test končan!")