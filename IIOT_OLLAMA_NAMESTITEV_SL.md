# IIoT Integracija z Ollama AI - Navodila za Namestitev

## 🎯 Pregled

Integracija industrijskega IoT (IIoT) z Ollama AI za analizo podatkov senzorjev v realnem času z uporabo Google Cloud infrastrukture.

### Arhitektura

```
IoT Naprave → Pub/Sub Tema → Push Naročnina → Cloud Run (Ollama) → Rezultati Analize
```

---

## 🚀 Hitra Namestitev

### 1. Nastavite Okoljske Spremenljivke

```bash
export GCP_PROJECT_ID="vaš-projekt-id"
export GCP_REGION="europe-west1"
export OLLAMA_MODEL="llama3"
```

### 2. Namestitev Infrastrukture

Zaženite avtomatizirani skript:

```bash
chmod +x scripts/deploy-iiot-ollama.sh
./scripts/deploy-iiot-ollama.sh
```

Ta skript bo:
- Ustvaril Pub/Sub temo za IoT podatke
- Zgradil in naložil Ollama Docker sliko
- Namestil Ollamo na Cloud Run
- Nastavil račun storitve in dovoljenja
- Ustvaril Pub/Sub push naročnino

### 3. Preverite Namestitev

```bash
# Preverite Cloud Run storitev
gcloud run services describe ollama-ai-inference \
  --region=europe-west1 \
  --format='value(status.url)'

# Testirajte health endpoint
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://vaš-url-storitve/api/v1/iiot/health
```

---

## 📡 Konfiguracija Pub/Sub

### Ustvarjanje Teme

```bash
gcloud pubsub topics create iot-data-topic \
  --project=${GCP_PROJECT_ID}
```

### Ustvarjanje Push Naročnine

Naročnina samodejno sproži Cloud Run, ko prispejo IoT podatki:

```bash
SERVICE_URL=$(gcloud run services describe ollama-ai-inference \
  --region=${GCP_REGION} \
  --format='value(status.url)')

gcloud pubsub subscriptions create iot-to-ollama-trigger \
  --topic=iot-data-topic \
  --push-endpoint="${SERVICE_URL}/api/v1/iiot/webhook/pubsub" \
  --push-auth-service-account=ollama-runner@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --ack-deadline=300 \
  --message-retention-duration=7d
```

---

## 🐳 Konfiguracija Ollama Docker

### Dockerfile.ollama

Priložen `Dockerfile.ollama` ustvari optimiziran kontejner:

```dockerfile
FROM ollama/ollama:latest
ENV OLLAMA_MODELS=llama3
RUN ollama pull ${OLLAMA_MODELS}
EXPOSE 11434
CMD ["ollama", "serve"]
```

### Gradnja z Cloud Build

```bash
gcloud builds submit \
  --config=cloudbuild-ollama.yaml \
  --substitutions=_PROJECT_ID=${GCP_PROJECT_ID},_OLLAMA_MODEL=llama3
```

---

## ☁️ Namestitev na Cloud Run

### Ukaz za Namestitev

```bash
gcloud run deploy ollama-ai-inference \
  --image=gcr.io/${GCP_PROJECT_ID}/ollama-llm-service:latest \
  --platform=managed \
  --region=europe-west1 \
  --cpu=4 \
  --memory=8Gi \
  --timeout=300 \
  --concurrency=10 \
  --min-instances=0 \
  --max-instances=10 \
  --no-allow-unauthenticated \
  --set-env-vars="OLLAMA_MODEL=llama3,IIOT_OLLAMA_ENABLED=true"
```

### Možnosti Konfiguracije

| Parameter | Vrednost | Opis |
|-----------|----------|------|
| `--cpu` | 4 | Dodelitev CPU (priporočeno 2-8) |
| `--memory` | 8Gi | Dodelitev pomnilnika (4-16Gi) |
| `--timeout` | 300 | Maksimalni čas zahteve (sekunde) |
| `--concurrency` | 10 | Sočasne zahteve na instanco |
| `--min-instances` | 0 | Minimalno število instanc |
| `--max-instances` | 10 | Maksimalno število instanc |

---

## 📊 API Končne Točke

### 1. Obdelava IoT Dogodka

**POST** `/api/v1/iiot/events/analyze`

```bash
curl -X POST https://vaš-api-url/api/v1/iiot/events/analyze \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "stroj-a-001",
    "sensor_data": {
      "temperatura": 85.5,
      "vibracije": 92,
      "pritisk": 120,
      "rpm": 1800
    },
    "metadata": {
      "lokacija": "tovarna-nadstropje-2",
      "tip_stroja": "cnc_rezkar"
    }
  }'
```

**Odgovor:**
```json
{
  "device_id": "stroj-a-001",
  "timestamp": "2025-11-03T21:00:00Z",
  "sensor_data": {...},
  "analysis": {
    "ai_analysis": "Temperatura in vibracije so povišane...",
    "anomaly_detected": true,
    "severity": "medium",
    "recommended_action": "Načrtujte pregled vzdrževanja"
  },
  "alert": {
    "severity": "medium",
    "message": "Ravni vibracij so zaskrbljujoče",
    "recommended_action": "Načrtujte pregled vzdrževanja"
  }
}
```

### 2. Analiza Toka Senzorjev

**POST** `/api/v1/iiot/streams/analyze`

Podpira tri vrste analiz:
- `anomaly_detection` - Zazna neobičajne vzorce
- `predictive` - Napoveduje okvare in potrebe po vzdrževanju
- `trend` - Analizira trende zmogljivosti

### 3. Objava v Pub/Sub

**POST** `/api/v1/iiot/events/publish`

Objavi IoT dogodek v Google Cloud Pub/Sub za obdelavo.

### 4. Status Storitve

**GET** `/api/v1/iiot/status`

Preveri status IIoT storitve, vključno z Ollamo in Pub/Sub razpoložljivostjo.

---

## 🧪 Testiranje

### Objavite Testno Sporočilo

```bash
gcloud pubsub topics publish iot-data-topic \
  --message='{"device_id":"test-001","data":{"temperatura":85,"vibracije":90,"pritisk":110},"metadata":{"lokacija":"testni-laboratorij"}}' \
  --project=${GCP_PROJECT_ID}
```

### Ogled Dnevnikov

```bash
# Cloud Run dnevniki
gcloud run logs read ollama-ai-inference \
  --region=${GCP_REGION} \
  --limit=50
```

---

## 📈 Spremljanje

### Ključne Metrike

Spremljajte te metrike v Cloud Console:

- **Cloud Run**:
  - Latenca zahtev (cilj: <5s za analizo)
  - Uporaba CPU kontejnerja
  - Uporaba pomnilnika kontejnerja
  - Število zahtev
  - Stopnja napak

- **Pub/Sub**:
  - Nedobavljena sporočila
  - Starost najstarejšega nepotrjenega sporočila
  - Latenca push zahtev

---

## 💰 Optimizacija Stroškov

### Priporočila

1. **Minimalno Število Instanc**: Nastavite na 0 za razvoj, 1+ za produkcijo
2. **Sočasnost**: Povečajte na 20-50, če model lahko obdela
3. **CPU/Pomnilnik**: Začnite s 4 CPU / 8Gi, prilagodite glede na obremenitev
4. **Hranjenje Sporočil**: 7 dni je zadostnih za večino primerov
5. **Izbira Modela**: Uporabite manjše modele (gemma:2b) za prihranek

### Ocenjeni Stroški (Mesečno)

Na podlagi 1M zahtev/mesec:

- Cloud Run: ~50-100€
- Pub/Sub: ~40€
- Container Registry: ~5€
- **Skupaj**: ~95-145€/mesec

---

## 🔧 Odpravljanje Težav

### Težava: Cloud Run cold starts

**Rešitev**: Nastavite `--min-instances=1` ali uporabite warm-up zahteve

### Težava: Ollama model ni naložen

**Rešitev**: Preverite, ali je model povlečen v Dockerfile

### Težava: Pub/Sub sporočila se ne obdelujejo

**Rešitev**: Preverite status naročnine in dovoljenja računa storitve

### Težava: Visoka latenca pri analizi

**Rešitev**: 
- Povečajte dodelitev CPU/pomnilnika
- Razmislite o uporabi GPU
- Uporabite manjši/hitrejši model

---

## 🌍 Okoljske Spremenljivke

Konfigurirajte v Cloud Run:

```bash
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
GCP_PROJECT_ID=vaš-projekt-id
IOT_PUBSUB_TOPIC=iot-data-topic
IIOT_OLLAMA_ENABLED=true
```

---

## 📚 Dodatni Viri

- [Google Cloud Pub/Sub Dokumentacija](https://cloud.google.com/pubsub/docs)
- [Cloud Run Dokumentacija](https://cloud.google.com/run/docs)
- [Ollama Dokumentacija](https://ollama.ai/docs)
- Podrobna angleška dokumentacija: `IIOT_OLLAMA_DEPLOYMENT.md`

---

## 📝 Dnevnik Sprememb

### Različica 1.0.0 (2025-11-03)

- ✨ Začetna IIoT Ollama integracija
- ✨ Google Cloud Pub/Sub podpora
- ✨ Avtomatizacija namestitve Cloud Run
- ✨ Tri vrste analiz (anomalije, napovedna, trend)
- ✨ Webhook za push naročnine
- 📝 Celovita dokumentacija za namestitev

---

## ✅ Implementirano

Implementacija vključuje:

1. **IIoT Ollama Servis** (`backend/services/advanced_ai/iiot_ollama.py`)
   - Obdelava IoT dogodkov z AI analizo
   - Analiza tokov senzorjev
   - Objava v Pub/Sub
   - Tri vrste analiz

2. **API Routes** (`backend/routes/iiot_ollama_routes.py`)
   - 5 končnih točk za IIoT operacije
   - Webhook za Pub/Sub push naročnine
   - Health check končne točke

3. **Deployment Infrastruktura**
   - `Dockerfile.ollama` - Ollama Docker slika
   - `cloudbuild-ollama.yaml` - Cloud Build konfiguracija
   - `scripts/deploy-iiot-ollama.sh` - Avtomatizirani deployment skript

4. **Dokumentacija**
   - `IIOT_OLLAMA_DEPLOYMENT.md` - Angleška dokumentacija
   - `IIOT_OLLAMA_NAMESTITEV_SL.md` - Slovenska dokumentacija
