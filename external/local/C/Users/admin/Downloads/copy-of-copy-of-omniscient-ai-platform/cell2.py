import subprocess, shlex

REGION = "europe-west1"
print("> gcloud builds submit")
# Opomba: ta ukaz se mora zagnati v korenski mapi projekta, kjer je cloudbuild.dual.yaml
subprocess.run(shlex.split(f"gcloud builds submit --config cloudbuild.dual.yaml --substitutions=_ENV=prod,_REGION={REGION} ."), check=True)

def get_url(service, region="europe-west1"):
    return subprocess.check_output(shlex.split(f'gcloud run services describe {service} --region {region} --format="value(status.url)"'), text=True).strip()

backend_url = get_url("omni-backend")
frontend_url = get_url("omni-frontend")

print("\n✅ Build and deploy successful!")
print("------------------------------")
print("Backend URL:", backend_url)
print("Frontend URL:", frontend_url)

# (neobvezno) health-check
try:
    print("\n> Checking backend health...")
    subprocess.run(shlex.split(f'curl -s "{backend_url}/health"'), check=True)
    print("✅ Health-check OK.")
except Exception:
    print("⚠️ Health-check ni uspel ali endpoint ni na voljo.")