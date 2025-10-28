import os
import json
import shutil
import glob
import subprocess

def size_of_path(path):
    try:
        if not os.path.exists(path):
            return 0
        if os.path.isfile(path):
            return os.path.getsize(path)
        total = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except Exception:
                    pass
        return total
    except Exception:
        return 0

def gb(n):
    return round(n / (1024**3), 2)

def first_existing(*paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None

def main():
    report = {}
    # Drive summary
    try:
        total, used, free = shutil.disk_usage('C:\\')
        report['Drive'] = {
            'UsedGB': gb(total - free),
            'FreeGB': gb(free),
            'TotalGB': gb(total),
        }
    except Exception:
        report['Drive'] = None

    items = []
    def add_item(name, path, typ):
        sz = size_of_path(path)
        items.append({'Name': name, 'Path': path, 'Type': typ, 'SizeGB': gb(sz)})

    add_item('Recycle Bin', r'C:\$Recycle.Bin', 'System')
    add_item('Windows Installer cache', r'C:\Windows\Installer', 'System')
    add_item('Windows Update downloads', r'C:\Windows\SoftwareDistribution\Download', 'System')
    add_item('ProgramData', r'C:\ProgramData', 'System')
    add_item('Admin Temp', os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'), 'User')

    for sysf in [r'C:\hiberfil.sys', r'C:\pagefile.sys']:
        try:
            if os.path.exists(sysf):
                items.append({'Name': os.path.basename(sysf), 'Path': sysf, 'Type': 'SystemFile', 'SizeGB': gb(os.path.getsize(sysf))})
        except Exception:
            pass

    report['TopCandidates'] = sorted([i for i in items if i['SizeGB'] > 1], key=lambda x: x['SizeGB'], reverse=True)[:10]

    # VHDX search
    vhd_roots = [
        os.path.expandvars(r'%LOCALAPPDATA%\Docker\wsl'),
        os.path.expandvars(r'%LOCALAPPDATA%\Packages'),
        r'C:\ProgramData\Docker',
        r'C:\Users\Public\Documents\Hyper-V\Virtual Hard Disks',
        r'C:\Users\admin',
    ]
    vhdx = []
    for root in vhd_roots:
        if os.path.exists(root):
            try:
                for p in glob.glob(os.path.join(root, '**', '*.vhdx'), recursive=True):
                    try:
                        sz = os.path.getsize(p)
                        vhdx.append({'Path': p, 'SizeGB': gb(sz)})
                    except Exception:
                        pass
            except Exception:
                pass
    vhdx = sorted(vhdx, key=lambda x: x['SizeGB'], reverse=True)[:8]
    report['VHDX'] = vhdx

    # Downloads top files (exclude project)
    downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
    proj = r'C:\\Users\\admin\\Downloads\\copy-of-copy-of-omniscient-ai-platform'
    dl = []
    if os.path.exists(downloads):
        for root, dirs, files in os.walk(downloads):
            for f in files:
                fp = os.path.join(root, f)
                if fp.startswith(proj):
                    continue
                try:
                    dl.append({'Path': fp, 'SizeGB': gb(os.path.getsize(fp))})
                except Exception:
                    pass
    dl = sorted(dl, key=lambda x: x['SizeGB'], reverse=True)[:5]
    report['DownloadsTop'] = dl

    # Shadow storage text
    try:
        out = subprocess.check_output(['vssadmin', 'list', 'shadowstorage'], stderr=subprocess.STDOUT, text=True, timeout=10)
        report['ShadowStorage'] = '\n'.join(out.splitlines()[:20])
    except Exception:
        report['ShadowStorage'] = None

    # Top-level roots on C:\ to spot big buckets
    roots = [
        r'C:\\Windows', r'C:\\Program Files', r'C:\\Program Files (x86)', r'C:\\ProgramData', r'C:\\Users'
    ]
    root_sizes = []
    for rp in roots:
        root_sizes.append({'Path': rp, 'SizeGB': gb(size_of_path(rp))})
    report['RootSizes'] = sorted(root_sizes, key=lambda x: x['SizeGB'], reverse=True)

    # Breakdown of C:\Users\admin top subfolders
    user_root = r'C:\\Users\\admin'
    user_top = []
    if os.path.exists(user_root):
        try:
            for name in os.listdir(user_root):
                p = os.path.join(user_root, name)
                try:
                    sz = size_of_path(p)
                    user_top.append({'Path': p, 'SizeGB': gb(sz)})
                except Exception:
                    pass
            user_top = sorted(user_top, key=lambda x: x['SizeGB'], reverse=True)[:12]
        except Exception:
            pass
    report['UserAdminTop'] = user_top

    # Print and save
    print(json.dumps(report, indent=2))
    try:
        out_path = os.path.join(os.path.dirname(__file__), '_disk_report.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
    except Exception:
        pass

if __name__ == '__main__':
    main()