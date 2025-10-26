import os
import json
import subprocess
from datetime import datetime

# --- Nastavitve ---
deployment_dir = "deployment-packages"
status_file = "last_module.json"

modules = [
    "omni-platform-v1.0.0",
    "omni-desktop-v1.0.0",
    "omni-frontend-v1.0.0"
]

# --- Preberi zadnji modul ---
if os.path.exists(status_file):
    with open(status_file, "r") as f:
        status = json.load(f)
    last_module = status.get("last_module", modules[0])
    if last_module not in modules:
        last_module = modules[0]
else:
    last_module = modules[0]

# --- Samodejni prehod na naslednji modul, če je potrebno ---
index = modules.index(last_module)
module_to_run = modules[index]  # Lahko spremeniš logiko, če hočeš vedno naslednji

print(f"Auto-launching module: {module_to_run}")

# --- Zagon modula ---
if module_to_run == "omni-platform-v1.0.0":
    exe_path = os.path.join(deployment_dir, module_to_run, "OMNI Platform.exe")
    if os.path.exists(exe_path):
        subprocess.Popen([exe_path])
elif module_to_run == "omni-desktop-v1.0.0":
    exe_path = os.path.join(deployment_dir, module_to_run, "win-unpacked", "OMNI AI Dashboard.exe")
    if os.path.exists(exe_path):
        subprocess.Popen([exe_path])
elif module_to_run == "omni-frontend-v1.0.0":
    frontend_dir = os.path.join(deployment_dir, module_to_run)
    print("Launching frontend on http://localhost:8000 ...")
    subprocess.Popen(["python", "-m", "http.server", "8000"], cwd=frontend_dir)

# --- Posodobi status ---
status_obj = {
    "last_module": module_to_run,
    "last_run": datetime.now().isoformat()
}
with open(status_file, "w") as f:
    json.dump(status_obj, f)

print(f"Status updated: {module_to_run} at {datetime.now()}")