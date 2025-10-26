import subprocess, shlex

def run(cmd):
    print("> ", cmd)
    p = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if p.stdout.strip(): print(p.stdout)
    if p.stderr.strip(): print(p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {cmd}\n{p.stderr}")
    return p.stdout.strip()

# Quick fix: Assign owner role (use with caution)
try:
    run('gcloud projects add-iam-policy-binding refined-graph-471712-n9 --member "serviceAccount:omni-runner@refined-graph-471712-n9.iam.gserviceaccount.com" --role "roles/owner"')
    print("✅ Owner role assigned.")
except Exception as e:
    print("⚠️ Failed to assign owner role:", e)

# Minimal roles for production
print("\nAssigning minimal roles...")

# Enable APIs
run('gcloud projects add-iam-policy-binding refined-graph-471712-n9 --member "serviceAccount:omni-runner@refined-graph-471712-n9.iam.gserviceaccount.com" --role "roles/serviceusage.serviceUsageAdmin"')

# Cloud Run & IAM
run('gcloud projects add-iam-policy-binding refined-graph-471712-n9 --member "serviceAccount:omni-runner@refined-graph-471712-n9.iam.gserviceaccount.com" --role "roles/run.admin"')
run('gcloud projects add-iam-policy-binding refined-graph-471712-n9 --member "serviceAccount:omni-runner@refined-graph-471712-n9.iam.gserviceaccount.com" --role "roles/iam.serviceAccountUser"')

# Artifact Registry
run('gcloud projects add-iam-policy-binding refined-graph-471712-n9 --member "serviceAccount:omni-runner@refined-graph-471712-n9.iam.gserviceaccount.com" --role "roles/artifactregistry.writer"')

# Cloud Build
run('gcloud projects add-iam-policy-binding refined-graph-471712-n9 --member "serviceAccount:omni-runner@refined-graph-471712-n9.iam.gserviceaccount.com" --role "roles/cloudbuild.builds.editor"')

# Secrets (if used)
run('gcloud projects add-iam-policy-binding refined-graph-471712-n9 --member "serviceAccount:omni-runner@refined-graph-471712-n9.iam.gserviceaccount.com" --role "roles/secretmanager.secretAccessor"')

print("✅ All IAM roles assigned successfully!")