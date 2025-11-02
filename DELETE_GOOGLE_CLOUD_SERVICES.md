# Brisanje Vseh Google Cloud Servisov - Navodila / Delete All Google Cloud Services - Instructions

⚠️ **OPOZORILO / WARNING**: Ta proces bo izbrisal VSE Google Cloud servise in lahko povzroči IZGUBO PODATKOV!
⚠️ **WARNING**: This process will delete ALL Google Cloud services and may cause DATA LOSS!

---

## Korak 1: Preveri kaj še teče / Step 1: Check What's Running

### Cloud Run Servisi / Cloud Run Services
```bash
# Prikaži vse Cloud Run servise
gcloud run services list --platform=managed

# Prikaži po regijah
gcloud run services list --platform=managed --region=europe-west1
gcloud run services list --platform=managed --region=us-central1
```

### Compute Engine VMs
```bash
# Prikaži vse VM instance
gcloud compute instances list

# Prikaži po regijah
gcloud compute instances list --zones=europe-west1-b
```

### Cloud SQL Baze / Cloud SQL Databases
```bash
# Prikaži vse SQL instance
gcloud sql instances list
```

### Cloud Storage Bucket-i / Cloud Storage Buckets
```bash
# Prikaži vse storage bucket-e
gcloud storage buckets list
```

### Kubernetes Clusters (GKE)
```bash
# Prikaži vse GKE cluster-je
gcloud container clusters list
```

### App Engine Aplikacije / App Engine Applications
```bash
# Prikaži App Engine servise
gcloud app services list
```

---

## Korak 2: Zbriši Cloud Run Servise / Step 2: Delete Cloud Run Services

### Zbriši posamezni servis / Delete individual service
```bash
# Primer / Example:
gcloud run services delete omni-dashboard --region=europe-west1 --quiet
gcloud run services delete omni-backend --region=europe-west1 --quiet
gcloud run services delete omni-frontend --region=europe-west1 --quiet
gcloud run services delete omni-api --region=europe-west1 --quiet
gcloud run services delete omni-monitoring --region=europe-west1 --quiet
```

### Zbriši VSE Cloud Run servise v regiji / Delete ALL Cloud Run services in region
```bash
# NEVARNO: Zbriše vse servise v europe-west1
# DANGEROUS: Deletes all services in europe-west1
for service in $(gcloud run services list --platform=managed --region=europe-west1 --format="value(name)"); do
  echo "Brišem / Deleting: $service"
  gcloud run services delete "$service" --region=europe-west1 --quiet
done
```

### Zbriši Cloud Run servise v VSEH regijah / Delete Cloud Run services in ALL regions
```bash
# ZELO NEVARNO: Zbriše VSE Cloud Run servise v VSEH regijah
# VERY DANGEROUS: Deletes ALL Cloud Run services in ALL regions
for region in $(gcloud run regions list --format="value(name)"); do
  echo "Preverjam regijo / Checking region: $region"
  for service in $(gcloud run services list --platform=managed --region=$region --format="value(name)"); do
    echo "Brišem / Deleting: $service v / in $region"
    gcloud run services delete "$service" --region=$region --quiet
  done
done
```

---

## Korak 3: Zbriši Compute Engine VMs

```bash
# Zbriši posamezno VM / Delete individual VM
gcloud compute instances delete INSTANCE_NAME --zone=ZONE --quiet

# Zbriši VSE VM instance / Delete ALL VM instances
for instance in $(gcloud compute instances list --format="value(name,zone)"); do
  name=$(echo $instance | cut -d' ' -f1)
  zone=$(echo $instance | cut -d' ' -f2)
  echo "Brišem VM / Deleting VM: $name v / in $zone"
  gcloud compute instances delete "$name" --zone="$zone" --quiet
done
```

---

## Korak 4: Zbriši Cloud SQL Instance

```bash
# Zbriši posamezno SQL instanco / Delete individual SQL instance
gcloud sql instances delete INSTANCE_NAME --quiet

# Zbriši VSE SQL instance / Delete ALL SQL instances
for instance in $(gcloud sql instances list --format="value(name)"); do
  echo "Brišem SQL / Deleting SQL: $instance"
  gcloud sql instances delete "$instance" --quiet
done
```

---

## Korak 5: Zbriši Cloud Storage Buckets

⚠️ **OPOZORILO**: To bo izbrisalo vse podatke v bucket-ih!
⚠️ **WARNING**: This will delete all data in buckets!

```bash
# Zbriši posamezni bucket / Delete individual bucket
gcloud storage rm -r gs://BUCKET_NAME

# Prikaži vse bucket-e / List all buckets
gcloud storage buckets list

# Zbriši VSE bucket-e (ZELO NEVARNO!)
# Delete ALL buckets (VERY DANGEROUS!)
for bucket in $(gcloud storage buckets list --format="value(name)"); do
  echo "Brišem bucket / Deleting bucket: $bucket"
  gcloud storage rm -r "gs://$bucket"
done
```

---

## Korak 6: Zbriši GKE Clusters

```bash
# Zbriši posamezen cluster / Delete individual cluster
gcloud container clusters delete CLUSTER_NAME --zone=ZONE --quiet

# Zbriši VSE cluster-je / Delete ALL clusters
for cluster in $(gcloud container clusters list --format="value(name,zone)"); do
  name=$(echo $cluster | cut -d' ' -f1)
  zone=$(echo $cluster | cut -d' ' -f2)
  echo "Brišem GKE cluster / Deleting GKE cluster: $name v / in $zone"
  gcloud container clusters delete "$name" --zone="$zone" --quiet
done
```

---

## Korak 7: Zbriši Container Registry Images

```bash
# Prikaži vse image-e / List all images
gcloud container images list

# Zbriši vse image-e v GCR / Delete all images in GCR
for image in $(gcloud container images list --format="value(name)"); do
  echo "Brišem image / Deleting image: $image"
  gcloud container images delete "$image" --quiet
done
```

---

## Korak 8: Onemogoči Cloud Build Trigger-je / Disable Cloud Build Triggers

```bash
# Prikaži vse trigger-je / List all triggers
gcloud builds triggers list

# Zbriši vse trigger-je / Delete all triggers
for trigger in $(gcloud builds triggers list --format="value(id)"); do
  echo "Brišem trigger / Deleting trigger: $trigger"
  gcloud builds triggers delete "$trigger" --quiet
done
```

---

## Korak 9: Preveri Cloud Billing / Check Cloud Billing

```bash
# Preveri billing račune / Check billing accounts
gcloud billing accounts list

# Preveri stroške / Check costs
gcloud billing accounts list --format="table(name,displayName)"
```

**Nato pojdi na / Then go to:**
- https://console.cloud.google.com/billing
- Preveri stroške in aktivne servise / Check costs and active services

---

## Korak 10: Popolni Pregled Vseh Servisov / Complete Overview of All Services

```bash
#!/bin/bash
# Skript za preverjanje vseh servisov
# Script to check all services

echo "=== CLOUD RUN SERVICES ==="
gcloud run services list --platform=managed

echo ""
echo "=== COMPUTE ENGINE VMs ==="
gcloud compute instances list

echo ""
echo "=== CLOUD SQL INSTANCES ==="
gcloud sql instances list

echo ""
echo "=== CLOUD STORAGE BUCKETS ==="
gcloud storage buckets list

echo ""
echo "=== GKE CLUSTERS ==="
gcloud container clusters list

echo ""
echo "=== CONTAINER IMAGES ==="
gcloud container images list | head -20

echo ""
echo "=== CLOUD BUILD TRIGGERS ==="
gcloud builds triggers list

echo ""
echo "=== APP ENGINE SERVICES ==="
gcloud app services list 2>/dev/null || echo "No App Engine services"

echo ""
echo "=== CLOUD FUNCTIONS ==="
gcloud functions list 2>/dev/null || echo "No Cloud Functions"
```

Shrani ta skript kot `check_all_services.sh` in poženi:
Save this script as `check_all_services.sh` and run:

```bash
chmod +x check_all_services.sh
./check_all_services.sh
```

---

## ⚡ Hiter Skript Za Brisanje Vsega / Quick Script to Delete Everything

⚠️ **ZELO NEVARNO - UPORABI NA LASTNO ODGOVORNOST!**
⚠️ **VERY DANGEROUS - USE AT YOUR OWN RISK!**

```bash
#!/bin/bash
# delete_all_google_cloud.sh

set -e

echo "⚠️  OPOZORILO: Ta skript bo ZBRISAL VSE Google Cloud servise!"
echo "⚠️  WARNING: This script will DELETE ALL Google Cloud services!"
echo ""
read -p "Si prepričan? Vpiši 'YES DELETE EVERYTHING' za potrditev: " confirmation

if [ "$confirmation" != "YES DELETE EVERYTHING" ]; then
  echo "Preklicano / Cancelled"
  exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
echo "Brišem vse servise v projektu / Deleting all services in project: $PROJECT_ID"

# Cloud Run
echo "1. Brišem Cloud Run servise / Deleting Cloud Run services..."
for region in $(gcloud run regions list --format="value(name)"); do
  for service in $(gcloud run services list --platform=managed --region=$region --format="value(name)"); do
    echo "  Brišem / Deleting: $service v / in $region"
    gcloud run services delete "$service" --region=$region --quiet
  done
done

# Compute Engine
echo "2. Brišem Compute Engine VMs..."
for instance in $(gcloud compute instances list --format="value(name,zone)"); do
  name=$(echo $instance | cut -d' ' -f1)
  zone=$(echo $instance | cut -d' ' -f2)
  echo "  Brišem VM / Deleting VM: $name"
  gcloud compute instances delete "$name" --zone="$zone" --quiet
done

# Cloud SQL
echo "3. Brišem Cloud SQL instance..."
for instance in $(gcloud sql instances list --format="value(name)"); do
  echo "  Brišem SQL / Deleting SQL: $instance"
  gcloud sql instances delete "$instance" --quiet
done

# GKE Clusters
echo "4. Brišem GKE clusters..."
for cluster in $(gcloud container clusters list --format="value(name,zone)"); do
  name=$(echo $cluster | cut -d' ' -f1)
  zone=$(echo $cluster | cut -d' ' -f2)
  echo "  Brišem cluster / Deleting cluster: $name"
  gcloud container clusters delete "$name" --zone="$zone" --quiet
done

# Cloud Build Triggers
echo "5. Brišem Cloud Build trigger-je..."
for trigger in $(gcloud builds triggers list --format="value(id)"); do
  echo "  Brišem trigger / Deleting trigger: $trigger"
  gcloud builds triggers delete "$trigger" --quiet
done

echo ""
echo "✅ VSE ZBRISANO / ALL DELETED"
echo "Preveri še billing račun / Check billing account:"
echo "https://console.cloud.google.com/billing"
```

Shrani kot `delete_all_google_cloud.sh` in poženi:
Save as `delete_all_google_cloud.sh` and run:

```bash
chmod +x delete_all_google_cloud.sh
./delete_all_google_cloud.sh
```

---

## Preverjanje Po Brisanju / Verification After Deletion

Po brisanju preveri, da res ni več nič aktivnega:
After deletion, verify that nothing is active:

```bash
# Naj bi vrnilo prazno / Should return empty
gcloud run services list --platform=managed
gcloud compute instances list
gcloud sql instances list
gcloud container clusters list

# Preveri billing / Check billing
echo "Pojdi na / Go to: https://console.cloud.google.com/billing"
```

---

## Kaj Še Ostane / What Remains

Tudi po brisanju vseh servisov lahko še vedno imaš stroške za:
Even after deleting all services, you may still have costs for:

1. **Cloud Storage** - buckets in podatki / buckets and data
2. **Container Registry** - Docker image-i / Docker images
3. **Cloud Logging** - shranjevanje log-ov / log storage
4. **Cloud Monitoring** - metrike / metrics
5. **Artifact Registry** - artifact-i / artifacts
6. **Networking** - IP naslovi, load balancerji / IP addresses, load balancers

Preveri vse v konzoli / Check everything in console:
https://console.cloud.google.com

---

## Opombe / Notes

- **Vsi konfiguraciji so še vedno v GitHub repozitoriju** / All configurations are still in the GitHub repository
- **Lahko ponovno deployaš kadarkoli** / You can redeploy anytime
- **Odstranjanje `.DISABLED` suffixov bo ponovno vklopilo deploy** / Removing `.DISABLED` suffixes will re-enable deployment
- **Preveri billing vsak dan prvih nekaj dni** / Check billing daily for the first few days

---

## Podpora / Support

Če imaš težave ali vprašanja:
If you have issues or questions:

1. Preveri Google Cloud Console / Check Google Cloud Console
2. Preveri billing račun / Check billing account  
3. Kontaktiraj Google Cloud Support če še vedno vidiš stroške / Contact Google Cloud Support if you still see charges

**Vsi deployment konfiguraciji so onemogočeni v tem repozitoriju, tako da novi deployments ne bo.**
**All deployment configurations are disabled in this repository, so no new deployments will occur.**
