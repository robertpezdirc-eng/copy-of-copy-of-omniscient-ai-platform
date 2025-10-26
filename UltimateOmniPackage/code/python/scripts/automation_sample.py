"""
Primer PowerShell/Python skripta za varnostne kopije in sinhronizacijo.
Uporaba: prilagodite poti v CONFIG.
"""
import os
import shutil
from datetime import datetime

CONFIG = {
    "source": "../../docs",
    "backup_root": "../../backups",
}

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def backup():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(CONFIG["backup_root"], f"docs_backup_{ts}")
    ensure_dir(dest)
    shutil.copytree(CONFIG["source"], os.path.join(dest, "docs"))
    print(f"Backup končan: {dest}")

if __name__ == '__main__':
    backup()