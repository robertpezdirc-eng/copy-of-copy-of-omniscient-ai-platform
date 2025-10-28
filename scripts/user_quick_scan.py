import os, json

def size(path):
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        total = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
        return total
    except Exception:
        return 0

def gb(n):
    return round(n/ (1024**3), 2)

u = r'C:\\Users\\admin'
targets = [
    os.path.join(u, 'Downloads'),
    os.path.join(u, 'Videos'),
    os.path.join(u, 'Pictures'),
    os.path.join(u, 'Documents'),
    os.path.join(u, 'Desktop'),
    os.path.join(u, 'Saved Games'),
    os.path.join(u, 'OneDrive'),
    os.path.join(u, 'AppData', 'Local', 'Docker'),
    os.path.join(u, 'AppData', 'Local', 'Packages'),
    os.path.join(u, 'AppData', 'Local', 'Temp'),
    os.path.join(u, 'AppData', 'LocalLow'),
    os.path.join(u, 'AppData', 'Roaming'),
]

out = []
for t in targets:
    if os.path.exists(t):
        out.append({'Path': t, 'SizeGB': gb(size(t))})

out = sorted(out, key=lambda x: x['SizeGB'], reverse=True)
print(json.dumps(out, indent=2))