# IIoT Data Integration with Ollama on Google Cloud

## Pregled / Overview

Ta implementacija omogoča povezavo Industrial IoT (IIoT) podatkov z Ollama LLM modelom preko Google Cloud Platform storitev za skalabilno, event-driven analizo podatkov s senzorjev.

This implementation enables connecting Industrial IoT (IIoT) data with Ollama LLM model through Google Cloud Platform services for scalable, event-driven analysis of sensor data.

## Arhitektura / Architecture

```
IoT Naprave/Devices
       ↓
Google Cloud Pub/Sub (iot-data-topic)
       ↓
Push Subscription Trigger
       ↓
Cloud Run: IIoT Ollama Processor ─→ Ollama AI Inference (LLM)
       ↓
Pub/Sub (iot-analysis-results) / Alert System
```

### Komponente / Components

1. **Google Cloud Pub/Sub Topic**: `iot-data-topic`
   - Prejema podatke iz IoT naprav / Receives data from IoT devices
   - Asinhrono sporočanje / Asynchronous messaging
   - Skalabilno za ogromne količine podatkov / Scalable for massive data volumes

2. **Ollama Cloud Run Service**: `ollama-ai-inference`
   - Docker kontejner z Ollama in llama3 modelom
   - 4 CPU, 8GB RAM
   - Izvaja LLM sklepe / Runs LLM inference

3. **IIoT Processing Service**: `iiot-ollama-processor`
   - FastAPI aplikacija za obdelavo Pub/Sub sporočil
   - Pošilja podatke Ollami za analizo / Sends data to Ollama for analysis
   - 2 CPU, 4GB RAM

4. **Push Subscription**: `iot-to-ollama-trigger`
   - Avtomatsko sproži Cloud Run ob prihodu podatkov
   - Automatically triggers Cloud Run when data arrives

## Nastavitev / Setup

### Predpogoji / Prerequisites

```bash
# Nastavite projekt / Set project
export PROJECT_ID="refined-graph-471712-n9"
export REGION="europe-west1"

gcloud config set project ${PROJECT_ID}

# Omogočite potrebne API-je / Enable required APIs
gcloud services enable pubsub.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Korak 1: Postavitev Pub/Sub Infrastrukture

Zaženite skript za nastavitev:

```bash
./setup-iiot-pubsub.sh
```

Ta skript bo:
- Ustvaril Pub/Sub teme (topics)
- Nastavil service account
- Dodelil IAM vloge

### Korak 2: Postavitev Ollama Storitve

Zgradite in uvedite Ollama storitev na Cloud Run:

```bash
# Gradnja in uvajanje z Cloud Build
gcloud builds submit --config=cloudbuild.ollama.yaml

# Ali ročno:
export PROJECT_ID="refined-graph-471712-n9"
export REGION="europe-west1"

# Zgradite Docker podobo
gcloud builds submit --tag gcr.io/${PROJECT_ID}/ollama-llm-service

# Uvedite na Cloud Run
gcloud run deploy ollama-ai-inference \
  --image gcr.io/${PROJECT_ID}/ollama-llm-service \
  --platform managed \
  --region ${REGION} \
  --cpu 4 \
  --memory 8Gi \
  --no-allow-unauthenticated \
  --max-instances 10 \
  --min-instances 0 \
  --ingress all \
  --port 11434
```

**Opomba**: Gradnja lahko traja 20-30 minut zaradi prenosa modela llama3.

### Korak 3: Postavitev IIoT Processing Storitve

Zgradite in uvedite IIoT processing storitev:

```bash
# Gradnja in uvajanje z Cloud Build
gcloud builds submit --config=cloudbuild.iiot-ollama.yaml

# Ali ročno:
# 1. Pridobite Ollama URL
export OLLAMA_URL=$(gcloud run services describe ollama-ai-inference \
  --region=${REGION} \
  --format='value(status.url)')

# 2. Zgradite in uvedite
gcloud builds submit --tag gcr.io/${PROJECT_ID}/iiot-ollama-service

gcloud run deploy iiot-ollama-processor \
  --image gcr.io/${PROJECT_ID}/iiot-ollama-service \
  --platform managed \
  --region ${REGION} \
  --cpu 2 \
  --memory 4Gi \
  --no-allow-unauthenticated \
  --max-instances 10 \
  --min-instances 0 \
  --ingress all \
  --port 8080 \
  --set-env-vars OLLAMA_URL=${OLLAMA_URL},OLLAMA_MODEL=llama3
```

### Korak 4: Ustvarite Push Subscription

Po uvedbi storitev, ustvarite Pub/Sub subscription:

```bash
# Pridobite URL IIoT storitve
export SERVICE_URL=$(gcloud run services describe iiot-ollama-processor \
  --region=${REGION} \
  --format='value(status.url)')

# Ustvarite subscription
gcloud pubsub subscriptions create iot-to-ollama-trigger \
  --topic=iot-data-topic \
  --push-endpoint="${SERVICE_URL}/" \
  --push-auth-service-account=ollama-runner@${PROJECT_ID}.iam.gserviceaccount.com \
  --ack-deadline=600 \
  --message-retention-duration=7d
```

## Uporaba / Usage

### Pošiljanje IoT Podatkov / Sending IoT Data

Podatke lahko pošljete v Pub/Sub temo:

```bash
# Primer sporočila s senzorskimi podatki
gcloud pubsub topics publish iot-data-topic --message='{
  "device_id": "sensor-001",
  "sensor_type": "vibration",
  "timestamp": "2024-01-01T12:00:00Z",
  "measurements": {
    "vibration": 92,
    "temperature": 75,
    "pressure": 101.3
  }
}'
```

### Format Sporočila / Message Format

```json
{
  "device_id": "sensor-001",
  "sensor_type": "vibration|temperature|pressure|generic",
  "timestamp": "ISO8601 timestamp",
  "measurements": {
    "key1": value1,
    "key2": value2
  }
}
```

### Testiranje Direktno / Direct Testing

Za testiranje brez Pub/Sub:

```bash
# Pridobite URL
export SERVICE_URL=$(gcloud run services describe iiot-ollama-processor \
  --region=${REGION} \
  --format='value(status.url)')

# Pošljite direktno zahtevo
curl -X POST "${SERVICE_URL}/analyze" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -d '{
    "device_id": "sensor-001",
    "sensor_type": "vibration",
    "timestamp": "2024-01-01T12:00:00Z",
    "measurements": {
      "vibration": 92,
      "temperature": 75
    }
  }'
```

## Monitoring

### Preverjanje Zdravja / Health Checks

```bash
# IIoT Processing Service
curl "${SERVICE_URL}/health" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"

# Ollama Service
export OLLAMA_URL=$(gcloud run services describe ollama-ai-inference \
  --region=${REGION} \
  --format='value(status.url)')
  
curl "${OLLAMA_URL}/api/tags" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

### Ogled Logov / View Logs

```bash
# IIoT Processing Service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=iiot-ollama-processor" \
  --limit=50 \
  --format=json

# Ollama Service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ollama-ai-inference" \
  --limit=50 \
  --format=json
```

### Metrike / Metrics

V Google Cloud Console lahko spremljate:
- Število zahtev / Request count
- Latenca / Latency
- Poraba CPU in pomnilnika / CPU and memory usage
- Napake / Errors

## Optimizacija Stroškov / Cost Optimization

### Pay-per-use Model

Cloud Run zaračunava le za dejanski čas izvajanja:
- **Ollama Service**: Aktivira se samo ob analizi
- **IIoT Processor**: Aktivira se samo ob prejemu Pub/Sub sporočila
- **Min instances = 0**: Popolna ustavitev, ko ni prometa

### Priporočila / Recommendations

1. **Uporabite GPU za velike modele** (opcijsko):
   ```bash
   --accelerator type=NVIDIA_TESLA_T4,count=1
   ```

2. **Nastavite maksimalne instance**:
   ```bash
   --max-instances 10  # Omejite za nadzor stroškov
   ```

3. **Optimizirajte timeout**:
   ```bash
   --timeout 600s  # 10 minut za kompleksno analizo
   ```

4. **Uporabite manjše modele za manj zahtevne naloge**:
   - llama3:8b (privzeto, dobro razmerje hitrost/kakovost)
   - gemma:2b (hitrejši, manjši)
   - mistral:7b (alternativa)

## Nadgradnja / Upgrading

### Zamenjava LLM Modela / Changing LLM Model

Uredite `Dockerfile.ollama`:

```dockerfile
ENV OLLAMA_MODELS=mistral:7b
RUN ollama pull ${OLLAMA_MODELS}
```

Ponovno zgradite in uvedite:

```bash
gcloud builds submit --config=cloudbuild.ollama.yaml
```

### Skaliranje / Scaling

```bash
# Povečajte resurse
gcloud run services update iiot-ollama-processor \
  --region=${REGION} \
  --cpu 4 \
  --memory 8Gi \
  --max-instances 20

# Za GPU podporo (Ollama)
gcloud run services update ollama-ai-inference \
  --region=${REGION} \
  --gpu 1 \
  --gpu-type nvidia-tesla-t4
```

## Odpravljanje Težav / Troubleshooting

### Pub/Sub sporočila se ne obdelujejo

1. Preverite subscription:
   ```bash
   gcloud pubsub subscriptions describe iot-to-ollama-trigger
   ```

2. Preverite IAM dovoljenja:
   ```bash
   gcloud projects get-iam-policy ${PROJECT_ID} \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:ollama-runner@${PROJECT_ID}.iam.gserviceaccount.com"
   ```

3. Preverite loge za napake:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" --limit=50
   ```

### Ollama timeout

Če analiza traja predolgo:

1. Povečajte timeout subscription:
   ```bash
   gcloud pubsub subscriptions update iot-to-ollama-trigger \
     --ack-deadline=600
   ```

2. Uporabite manjši/hitrejši model
3. Dodajte GPU podporo

### Stroški so previsoki

1. Preverite število instance:
   ```bash
   gcloud run services describe iiot-ollama-processor --region=${REGION}
   ```

2. Nastavite min-instances na 0:
   ```bash
   gcloud run services update iiot-ollama-processor \
     --region=${REGION} \
     --min-instances 0
   ```

3. Zmanjšajte max-instances za omejevanje stroškov

## Varnost / Security

### Best Practices

1. **Ne dovoli javnega dostopa**:
   - Vse storitve so nastavljene z `--no-allow-unauthenticated`
   - Dostop samo preko service account

2. **Uporabite Secret Manager za občutljive podatke**:
   ```bash
   # Shrani API ključe v Secret Manager
   echo -n "api-key" | gcloud secrets create iiot-api-key --data-file=-
   
   # Referenciraj v Cloud Run
   --set-secrets=API_KEY=iiot-api-key:latest
   ```

3. **Omogočite VPC Connector** za privatno komunikacijo med storitvami

4. **Redno posodabljajte Docker podobe**

## Dodatna Dokumentacija / Additional Documentation

- [Google Cloud Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Ollama Documentation](https://ollama.ai/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Podpora / Support

Za vprašanja ali težave, odprite issue v repozitoriju.
