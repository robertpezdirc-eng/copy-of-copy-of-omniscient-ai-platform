#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 OMNI Learning Overlay - Launcher
Zažene sistem za učenje v ozadju
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Zaženi OMNI Learning Overlay"""
    print("🌐 OMNI Learning Overlay Launcher")
    print("🚀 Začenjam sistem za avtonomno učenje...")

    # Preveri če so potrebne datoteke
    required_files = [
        "background_learning.py",
        "analytics.py",
        "omni_core_api.py",
        "overlay_config.json"
    ]

    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Manjka datoteka: {file}")
            return False

    try:
        # Zaženi background learning
        print("📚 Začenjam background learning...")
        subprocess.Popen([sys.executable, "background_learning.py"])

        print("✅ OMNI Learning Overlay je aktiven!")
        print("🎯 Agenti se bodo učili vsako uro")
        print("📊 Statistiko lahko spremljate preko analytics.py")
        print("🛑 Za zaustavitev pritisnite Ctrl+C")

        # Obdrži proces aktiven
        try:
            while True:
                input("Pritisnite Enter za izhod...\n")
                break
        except KeyboardInterrupt:
            print("\n🛑 Zaustavljanje OMNI Learning Overlay...")

    except Exception as e:
        print(f"❌ Napaka pri zagonu: {e}")
        return False

    return True

if __name__ == "__main__":
    main()