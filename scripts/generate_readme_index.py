import os
import json
import time
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
# Go up from scripts/ to repo root
REPO_ROOT = os.path.abspath(os.path.join(ROOT, os.pardir))

EXCLUDE_DIRS = {
    '.git', '.venv', 'node_modules', 'dist', 'build', '__pycache__',
    '.pytest_cache', '.firebase'
}

OUTPUT_JSON = os.path.join(REPO_ROOT, 'docs_index.json')
OUTPUT_MD = os.path.join(REPO_ROOT, 'DOCS_INDEX.md')

MD_EXTENSIONS = {'.md', '.markdown', '.mdx'}
READMES = {'README.md', 'README', 'readme.md', 'Readme.md'}

HOURS_WINDOW = 48


def should_exclude(path):
    parts = path.replace('\\', '/').split('/')
    return any(p in EXCLUDE_DIRS for p in parts)


def find_md_files(root_dir):
    entries = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter excluded directories in-place to skip walking into them
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        if should_exclude(dirpath):
            continue
        for fname in filenames:
            fext = os.path.splitext(fname)[1].lower()
            if fext in MD_EXTENSIONS or fname in READMES:
                fpath = os.path.join(dirpath, fname)
                try:
                    stat = os.stat(fpath)
                    entries.append({
                        'path': os.path.relpath(fpath, root_dir).replace('\\', '/'),
                        'abs_path': fpath,
                        'size': stat.st_size,
                        'mtime': stat.st_mtime,
                        'mtime_dt': datetime.fromtimestamp(stat.st_mtime).isoformat(timespec='seconds')
                    })
                except Exception:
                    # Skip unreadable files
                    pass
    return entries


def group_by_top_level(entries):
    grouped = {}
    for e in entries:
        parts = e['path'].split('/')
        top = parts[0] if parts else ''
        grouped.setdefault(top, []).append(e)
    return grouped


def compute_recent_changes(entries, hours=HOURS_WINDOW):
    cutoff = time.time() - hours * 3600
    recent = [e for e in entries if e['mtime'] >= cutoff]
    recent.sort(key=lambda x: x['mtime'], reverse=True)
    return recent


def write_json_index(entries, recent):
    data = {
        'generated_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'total_count': len(entries),
        'recent_window_hours': HOURS_WINDOW,
        'recent_count': len(recent),
        'files': entries,
        'recent_files': recent
    }
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_markdown_index(grouped, recent):
    lines = []
    total = sum(len(v) for v in grouped.values())
    lines.append('# Documentation Index (Auto-generated)')
    lines.append('')
    lines.append(f'- Generated at: {datetime.utcnow().isoformat(timespec="seconds")}Z')
    lines.append(f'- Total markdown files: {total}')
    lines.append(f'- Recent changes (last {HOURS_WINDOW}h): {len(recent)}')
    lines.append('')

    # Recent section
    lines.append('## Recent Changes (last 48h)')
    if recent:
        for e in recent[:200]:
            lines.append(f'- `{e["path"]}` — {e["mtime_dt"]}')
    else:
        lines.append('- No recent changes found')
    lines.append('')

    # Grouped listing
    lines.append('## All Markdown Files by Top-level Folder')
    for top in sorted(grouped.keys()):
        lines.append(f'### {top or "/"}')
        for e in sorted(grouped[top], key=lambda x: x['path']):
            lines.append(f'- `{e["path"]}` (updated {e["mtime_dt"]})')
        lines.append('')

    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    print(f"Repo root: {REPO_ROOT}")
    entries = find_md_files(REPO_ROOT)
    grouped = group_by_top_level(entries)
    recent = compute_recent_changes(entries)

    write_json_index(entries, recent)
    write_markdown_index(grouped, recent)

    print(f"Written JSON index: {OUTPUT_JSON}")
    print(f"Written Markdown index: {OUTPUT_MD}")
    print(f"Total files: {len(entries)}; Recent: {len(recent)}")


if __name__ == '__main__':
    main()