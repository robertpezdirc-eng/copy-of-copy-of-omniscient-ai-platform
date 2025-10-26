import os
import json
from datetime import datetime, timedelta

# ---- Konfiguracija ----
DEPLOY_DIR = r"C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform\deployment-packages"
MANIFEST_FILE = os.path.join(DEPLOY_DIR, "build_state.json")
DAYS_LOOKBACK = 7  # Koliko dni nazaj preverjamo gradnje

# ---- Funkcije ----
def scan_modules():
    """Pregleda deployment-packages in zabeleži gradnike."""
    modules = {}
    if not os.path.exists(DEPLOY_DIR):
        print("Deployment-packages mapa ne obstaja!")
        return modules

    for module_name in os.listdir(DEPLOY_DIR):
        module_path = os.path.join(DEPLOY_DIR, module_name)
        if os.path.isdir(module_path):
            latest_time = None
            for root, _, files in os.walk(module_path):
                for f in files:
                    full_path = os.path.join(root, f)
                    file_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                    if latest_time is None or file_time > latest_time:
                        latest_time = file_time
            modules[module_name] = {
                "last_build": latest_time.isoformat() if latest_time else None,
                "path": module_path
            }
    return modules

def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r") as f:
            return json.load(f)
    return {}

def save_manifest(data):
    with open(MANIFEST_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_recent_builds(modules, days=DAYS_LOOKBACK):
    cutoff = datetime.now() - timedelta(days=days)
    recent = {}
    for name, info in modules.items():
        if info["last_build"]:
            last_time = datetime.fromisoformat(info["last_build"])
            if last_time >= cutoff:
                recent[name] = info
    return recent

def display_modules(modules):
    print("\n=== Omni Paket - Moduli ===")
    for name, info in modules.items():
        print(f"{name}:")
        print(f"  Pot: {info['path']}")
        print(f"  Zadnja gradnja: {info['last_build']}")
    print("===========================\n")

# ---- Glavni program ----
if __name__ == "__main__":
    modules = scan_modules()
    manifest = load_manifest()

    # Posodobi manifest z aktualnimi gradnjami
    manifest.update(modules)
    save_manifest(manifest)

    # Pokaži vse module
    display_modules(modules)

    # Pokaži module, zgrajene v zadnjih X dni
    recent = get_recent_builds(modules)
    print(f"=== Moduli zgrajeni zadnjih {DAYS_LOOKBACK} dni ===")
    for name, info in recent.items():
        print(f"{name} (zadnja gradnja: {info['last_build']})")
    print("==============================================")