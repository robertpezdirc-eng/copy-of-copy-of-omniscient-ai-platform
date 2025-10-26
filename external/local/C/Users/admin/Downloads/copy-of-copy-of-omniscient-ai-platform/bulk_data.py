import subprocess, shlex, json

def run(cmd):
    print(f"> {cmd}")
    p = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if p.stdout.strip(): print(p.stdout)
    if p.stderr.strip(): print(p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {cmd}\n{p.stderr}")
    return p.stdout.strip()

print("=== omni-backend Status ===")
try:
    status = run('gcloud run services describe omni-backend --region europe-west1 --format="json"')
    print(json.dumps(json.loads(status), indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n=== omni-backend Logs ===")
try:
    logs = run('gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=omni-backend" --project=refined-graph-471712-n9 --format=json --limit=20')
    print(json.dumps(json.loads(logs), indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n=== omni-frontend Status ===")
try:
    status = run('gcloud run services describe omni-frontend --region europe-west1 --format="json"')
    print(json.dumps(json.loads(status), indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n=== omni-frontend Logs ===")
try:
    logs = run('gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=omni-frontend" --project=refined-graph-471712-n9 --format=json --limit=20')
    print(json.dumps(json.loads(logs), indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n=== Cloud Builds ===")
try:
    builds = run('gcloud builds list --project=refined-graph-471712-n9 --format=json --limit=5')
    print(json.dumps(json.loads(builds), indent=2))
except Exception as e:
    print(f"Error: {e}")