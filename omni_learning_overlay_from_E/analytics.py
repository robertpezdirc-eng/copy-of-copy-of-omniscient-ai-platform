#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 OMNI Learning Overlay - Analytics Module
Vrača podatke o učenju in znanju agentov
"""

import json
import os
from datetime import datetime, timedelta

class LearningAnalytics:
    def __init__(self, memory_folder="omni_learning_overlay/memory"):
        self.memory_folder = memory_folder

    def get_agent_memory(self, agent_id):
        """Pridobi spomin določenega agenta"""
        file_path = f"{self.memory_folder}/{agent_id}.json"

        if not os.path.exists(file_path):
            return {
                "agent": agent_id,
                "learned_topics": 0,
                "latest_focus": None,
                "last_learning": None,
                "total_sessions": 0
            }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                memory = json.load(f)

            if not memory:
                return {
                    "agent": agent_id,
                    "learned_topics": 0,
                    "latest_focus": None,
                    "last_learning": None,
                    "total_sessions": 0
                }

            # Analiziraj spomin
            learned_topics = len(memory)
            latest_entry = memory[-1]
            last_learning = latest_entry.get('timestamp')

            # Preštej edinstvene teme
            unique_topics = set(entry.get('topic') for entry in memory)

            return {
                "agent": agent_id,
                "learned_topics": learned_topics,
                "unique_topics": len(unique_topics),
                "latest_focus": latest_entry.get('topic'),
                "last_learning": last_learning,
                "total_sessions": learned_topics,
                "memory_size": self.get_memory_size(memory)
            }

        except Exception as e:
            print(f"❌ Napaka pri branju spomina agenta {agent_id}: {e}")
            return {
                "agent": agent_id,
                "error": str(e)
            }

    def get_all_agents_memory(self):
        """Pridobi spomin vseh agentov"""
        agents_memory = {}

        try:
            if not os.path.exists(self.memory_folder):
                return {"agents": {}, "total_learned_topics": 0}

            for filename in os.listdir(self.memory_folder):
                if filename.endswith('.json'):
                    agent_id = filename[:-5]  # Odstrani .json
                    agent_memory = self.get_agent_memory(agent_id)
                    agents_memory[agent_id] = agent_memory

            total_topics = sum(agent.get('learned_topics', 0) for agent in agents_memory.values())

            return {
                "agents": agents_memory,
                "total_learned_topics": total_topics,
                "total_agents": len(agents_memory),
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Napaka pri pridobivanju spomina vseh agentov: {e}")
            return {"error": str(e)}

    def get_learning_progress(self, days=7):
        """Pridobi napredek učenja za zadnjih X dni"""
        progress = {}
        start_date = datetime.now() - timedelta(days=days)

        try:
            if not os.path.exists(self.memory_folder):
                return {"progress": [], "total_learned": 0}

            total_learned = 0

            for filename in os.listdir(self.memory_folder):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.memory_folder, filename)

                    with open(file_path, 'r', encoding='utf-8') as f:
                        memory = json.load(f)

                    # Filtriraj vnose po datumu
                    for entry in memory:
                        entry_date = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))

                        if entry_date >= start_date:
                            date_str = entry_date.strftime('%Y-%m-%d')

                            if date_str not in progress:
                                progress[date_str] = 0
                            progress[date_str] += 1
                            total_learned += 1

            # Pretvori v seznam za lažjo uporabo
            progress_list = [
                {"date": date, "topics_learned": count}
                for date, count in sorted(progress.items())
            ]

            return {
                "progress": progress_list,
                "total_learned": total_learned,
                "period_days": days
            }

        except Exception as e:
            print(f"❌ Napaka pri pridobivanju napredka: {e}")
            return {"error": str(e)}

    def get_memory_size(self, memory):
        """Pridobi velikost spomina v bajtih"""
        return len(json.dumps(memory, ensure_ascii=False).encode('utf-8'))

    def cleanup_old_memory(self, retention_days=30):
        """Počisti star spomin"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cleaned_count = 0

            for filename in os.listdir(self.memory_folder):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.memory_folder, filename)

                    with open(file_path, 'r', encoding='utf-8') as f:
                        memory = json.load(f)

                    # Filtriraj stare vnose
                    filtered_memory = [
                        entry for entry in memory
                        if datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')) > cutoff_date
                    ]

                    # Shrani filtriran spomin
                    if len(filtered_memory) != len(memory):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(filtered_memory, f, indent=2, ensure_ascii=False)
                        cleaned_count += (len(memory) - len(filtered_memory))

            return {
                "cleaned_entries": cleaned_count,
                "retention_days": retention_days
            }

        except Exception as e:
            print(f"❌ Napaka pri čiščenju spomina: {e}")
            return {"error": str(e)}

# API funkcije za zunanjo uporabo
def get_agent_memory(agent_id):
    """API funkcija za pridobitev spomina agenta"""
    analytics = LearningAnalytics()
    return analytics.get_agent_memory(agent_id)

def get_all_agents_memory():
    """API funkcija za pridobitev spomina vseh agentov"""
    analytics = LearningAnalytics()
    return analytics.get_all_agents_memory()

def get_learning_progress(days=7):
    """API funkcija za pridobitev napredka učenja"""
    analytics = LearningAnalytics()
    return analytics.get_learning_progress(days)

def cleanup_old_memory(retention_days=30):
    """API funkcija za čiščenje starega spomina"""
    analytics = LearningAnalytics()
    return analytics.cleanup_old_memory(retention_days)

if __name__ == "__main__":
    # Test funkcionalnosti
    print("🧪 Testiranje OMNI Learning Analytics...")

    analytics = LearningAnalytics()

    # Test 1: Pridobi spomin vseh agentov
    print("\n📊 Test 1: Spomin vseh agentov")
    all_memory = analytics.get_all_agents_memory()
    print(f"Total agents: {all_memory.get('total_agents', 0)}")
    print(f"Total topics learned: {all_memory.get('total_learned_topics', 0)}")

    # Test 2: Napredek učenja
    print("\n📈 Test 2: Napredek učenja (zadnjih 7 dni)")
    progress = analytics.get_learning_progress(7)
    print(f"Topics learned in period: {progress.get('total_learned', 0)}")

    # Test 3: Počisti star spomin
    print("\n🧹 Test 3: Čiščenje spomina")
    cleanup = analytics.cleanup_old_memory(30)
    print(f"Cleaned entries: {cleanup.get('cleaned_entries', 0)}")

    print("\n✅ Test končan!")