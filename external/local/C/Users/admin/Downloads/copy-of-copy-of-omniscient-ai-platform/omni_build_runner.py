import os
import json
import subprocess
from datetime import datetime

# Nastavi pot do deployment-packages
BASE_PATH = r"C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform\deployment-packages"
STATE_FILE = os.path.join(BASE_PATH, "omni_build_state.json")

# Poišči glavne .exe in .html datoteke za vsak modul
def scan_builds():
    modules = {}
    for module in os.listdir(BASE_PATH):
        module_path = os.path.join(BASE_PATH, module)
        if os.path.isdir(module_path):
            latest_file = None
            latest_time = None
            for root, _, files in os.walk(module_path):
                for f in files:
                    if f.endswith((".exe", ".html")):
                        full_path = os.path.join(root, f)
                        mod_time = os.path.getmtime(full_path)
                        if latest_time is None or mod_time > latest_time:
                            latest_time = mod_time
                            latest_file = full_path
            if latest_file:
                modules[module] = {
                    "path": latest_file,
                    "last_build": datetime.fromtimestamp(latest_time).isoformat(),
                    "status": "built"
                }
            else:
                modules[module] = {
                    "path": None,
                    "last_build": None,
                    "status": "missing"
                }
    return modules

# Shrani stanje v json
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)
    print(f"\nStanje shranjeno v {STATE_FILE}\n")

# Naloži prejšnje stanje
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

# Prikaži stanje in izberi modul za zagon
def show_state_and_run(state):
    print("Pregled gradnikov Omni platforme:\n")
    modules_list = list(state.items())
    for i, (module, info) in enumerate(modules_list, 1):
        status = info["status"]
        path = info["path"] or "Ni datoteke"
        last_build = info["last_build"] or "Ni datuma"
        print(f"{i}. {module}:\n   Status: {status}\n   Pot: {path}\n   Zadnja gradnja: {last_build}\n")

    # Poišči zadnji zgrajeni modul
    built_modules = [info for module, info in modules_list if info["status"] == "built"]
    if not built_modules:
        print("Ni zgrajenih modulov za zagon.")
        return

    # Najdi zadnji zgrajen modul po času
    last_module = max(built_modules, key=lambda x: x["last_build"])
    exe_path = last_module["path"]
    print(f"Najbolj svež modul za zagon: {exe_path}\n")

    # Zaženi .exe ali odpri .html
    if exe_path.endswith(".exe"):
        print(f"Zagon {exe_path}...")
        subprocess.Popen([exe_path])
    elif exe_path.endswith(".html"):
        print(f"Odpiranje v brskalniku: {exe_path}...")
        os.startfile(exe_path)
    else:
        print("Ni primerne datoteke za zagon.")

# Glavna funkcija
def main():
    state = scan_builds()
    save_state(state)
    show_state_and_run(state)

if __name__ == "__main__":
    main()