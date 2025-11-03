# AI/ML Nadgradnje - Vodnik za Implementacijo

## 🎯 Pregled

Ta dokument opisuje napredne AI/ML nadgradnje, implementirane za platformo Omni Enterprise Ultra Max, ki obravnavajo naslednje zahteve:

1. **Pametnejši modeli** - Napredni LLM in multimodalni modeli
2. **Automatiziran MLOps pipeline** - Neprekinjeno učenje, testiranje in uvajanje
3. **Generiranje vsebine** - Samodejno generiranje dokumentacije, testnih podatkov in funkcionalnosti

---

## 🚀 Nove Funkcionalnosti

### 1. Avtomatizacija MLOps Pipeline

Popolnoma avtomatiziran MLOps pipeline, ki upravlja celoten življenjski cikel strojnega učenja.

#### Ključne Zmožnosti

- **Avtomatizirano Učenje**: Razpored učenja modelov (urno, dnevno, tedensko)
- **Validacija**: Avtomatska evalvacija modela glede na pragove kakovosti
- **Auto-Uvajanje**: Uvajanje modelov, ki izpolnjujejo kriterije kakovosti
- **Spremljanje**: Sledenje metrikam uspešnosti in trendom skozi čas
- **Opozarjanje**: Nastavljivі pragovi za degradacijo uspešnosti

#### API Končne Točke

##### Ustvarjanje MLOps Pipeline
```http
POST /api/v1/advanced-ai/mlops/pipelines
```

**Zahteva:**
```json
{
  "model_name": "napovedovalec_prihodkov",
  "dataset_uri": "gs://omni-data/podatki_prodaje.csv",
  "target_metric": "accuracy",
  "threshold": 0.85,
  "auto_deploy": true,
  "schedule": "daily"
}
```

**Odgovor:**
```json
{
  "id": "pipeline-uuid",
  "model_name": "napovedovalec_prihodkov",
  "status": "active",
  "created_at": "2025-11-03T21:00:00Z",
  "next_run": "2025-11-04T21:00:00Z",
  "total_runs": 0
}
```

##### Ročno Sprožitev Pipeline
```http
POST /api/v1/advanced-ai/mlops/pipelines/{pipeline_id}/trigger
```

##### Preverjanje Statusa Pipeline
```http
GET /api/v1/advanced-ai/mlops/pipelines/{pipeline_id}
```

**Odgovor:**
```json
{
  "id": "pipeline-uuid",
  "model_name": "napovedovalec_prihodkov",
  "status": "active",
  "total_runs": 5,
  "latest_run": {
    "id": "run-uuid",
    "status": "deployed",
    "metrics": {
      "accuracy": 0.9234,
      "loss": 0.2156
    },
    "artifacts": {
      "model_uri": "gs://omni-models/napovedovalec_prihodkov/v5/model.pkl",
      "version": "v5"
    }
  }
}
```

---

### 2. Servis za Generiranje Vsebine

AI-poganjano generiranje vsebine za dokumentacijo, testne podatke in predloge funkcionalnosti.

#### Ključne Zmožnosti

- **Generiranje Dokumentacije**: Ustvarjanje dokumentacije iz kode v različnih formatih
- **Generiranje Testnih Podatkov**: Generiranje realističnih testnih podatkov iz shem
- **Predlogi Funkcionalnosti**: AI-voden predlogi funkcionalnosti
- **API Primeri**: Primeri kode v več programskih jezikih

#### API Končne Točke

##### Generiranje Dokumentacije
```http
POST /api/v1/advanced-ai/content/documentation
```

**Zahteva:**
```json
{
  "code_snippet": "def izracunaj_prihodke(prodaja, stroski):\n    return prodaja - stroski",
  "language": "python",
  "doc_format": "markdown",
  "include_examples": true
}
```

**Odgovor:**
```json
{
  "documentation": "# API Dokumentacija\n\n## izracunaj_prihodke\n\n...",
  "format": "markdown",
  "language": "python",
  "entities_found": ["izracunaj_prihodke"],
  "generated_at": "2025-11-03T21:00:00Z",
  "char_count": 542,
  "confidence": 0.94
}
```

Podprti formati:
- `markdown` - Markdown dokumentacija
- `docstring` - Python docstrings
- `openapi` - OpenAPI specifikacija

##### Generiranje Testnih Podatkov
```http
POST /api/v1/advanced-ai/content/test-data
```

**Zahteva:**
```json
{
  "schema": {
    "uporabnik_id": "uuid",
    "ime": "string",
    "email": "email",
    "starost": "integer",
    "aktiven": "boolean",
    "ustvarjen_ob": "timestamp"
  },
  "count": 100,
  "seed": 42
}
```

Podprti tipi polj:
- `string`, `integer`, `float`, `boolean`
- `email`, `uuid`, `timestamp`

##### Generiranje Predlogov Funkcionalnosti
```http
POST /api/v1/advanced-ai/content/feature-suggestions
```

**Zahteva:**
```json
{
  "context": {
    "usage_patterns": {
      "api_calls_per_hour": 1500,
      "error_rate": 0.08
    },
    "current_features": ["avtentikacija", "api"],
    "user_feedback": ["Potrebujemo boljšo zmogljivost", "Dodajte omejitev klicanja"]
  },
  "max_suggestions": 5
}
```

**Odgovor:**
```json
{
  "suggestions": [
    {
      "title": "Izboljšano Obravnavanje Napak",
      "description": "Stopnja napak nad pragom. Izboljšajte sporočila o napakah in obnovitev.",
      "priority": 95,
      "effort": "low",
      "impact": "high",
      "source": "usage_analysis"
    },
    {
      "title": "Implementacija Nivojev Omejitve Klicanja",
      "description": "Zaznana visoka uporaba API. Razmislite o implementaciji nivojev omejitve.",
      "priority": 90,
      "effort": "medium",
      "impact": "high"
    }
  ],
  "count": 2,
  "generated_at": "2025-11-03T21:00:00Z"
}
```

##### Generiranje API Primerov
```http
POST /api/v1/advanced-ai/content/api-examples
```

**Zahteva:**
```json
{
  "endpoint": "/api/v1/uporabniki",
  "method": "POST",
  "parameters": {
    "ime": "Janez Novak",
    "email": "janez@example.com"
  }
}
```

**Odgovor:**
```json
{
  "endpoint": "/api/v1/uporabniki",
  "method": "POST",
  "examples": {
    "curl": "curl -X POST \"https://api.example.com/api/v1/uporabniki\" ...",
    "python": "import requests\n\nurl = \"https://api.example.com/api/v1/uporabniki\" ...",
    "javascript": "const response = await fetch(...) ...",
    "go": "package main\n\nimport (...) ..."
  },
  "generated_at": "2025-11-03T21:00:00Z"
}
```

---

### 3. Izboljšan Multimodalni AI

Napredne multimodalne zmožnosti z uporabo najsodobnejših AI modelov.

#### Ključne Zmožnosti

- **Analiza Vizualnih Elementov**: Analiziranje slik z GPT-4 Vision
- **Generiranje Slik**: Ustvarjanje slik z DALL-E 3
- **Transkripcija Zvoka**: Pretvarjanje govora v besedilo z Whisper
- **Besedilo v Govor**: Generiranje naravnega govora s TTS modeli
- **Multimodalna Fuzija**: Kombiniranje vpogledov iz besedila, slike in zvoka

#### API Končne Točke

##### Analiza Multimodalne Vsebine
```http
POST /api/v1/advanced-ai/multimodal/analyze
```

**Zahteva:**
```json
{
  "text": "Povratne informacije strank o nadzorni plošči",
  "image_url": "https://example.com/posnetek-zaslona.png",
  "audio_url": "https://example.com/klic-stranke.mp3",
  "metadata": {
    "tenant_id": "acme-corp"
  }
}
```

**Odgovor:**
```json
{
  "timestamp": "2025-11-03T21:00:00Z",
  "modalities": ["text", "image", "audio"],
  "text_summary": {
    "snippet": "Povratne informacije strank o nadzorni plošči...",
    "sentiment": "positive",
    "keywords": ["plošča", "povratne", "stranke"],
    "ai_analysis": "Podrobna AI analiza..."
  },
  "image_tags": [
    {
      "label": "analitična nadzorna plošča",
      "confidence": 0.92,
      "source": "ai"
    }
  ],
  "audio_transcript": {
    "transcript": "AI-poganjana transkripcija...",
    "language": "sl",
    "confidence": 0.95
  },
  "insights": [
    "Sentiment strank se nagiba k pozitivnemu",
    "Vizualni elementi poudarjajo analitične plošče"
  ],
  "confidence": 0.89
}
```

##### Generiranje Slike
```http
POST /api/v1/advanced-ai/multimodal/generate-image
```

**Zahteva:**
```json
{
  "prompt": "Moderna analitična nadzorna plošča z grafikoni in diagrami",
  "size": "1024x1024",
  "quality": "standard"
}
```

Podprte velikosti: `1024x1024`, `1792x1024`, `1024x1792`
Podprta kakovost: `standard`, `hd`

##### Pretvorba Besedila v Govor
```http
POST /api/v1/advanced-ai/multimodal/text-to-speech
```

**Zahteva:**
```json
{
  "text": "Dobrodošli na platformi Omni Enterprise Ultra Max",
  "voice": "alloy",
  "model": "tts-1"
}
```

Podprti glasovi: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

---

## 🏗️ Arhitektura

### Struktura Servisov

```
backend/services/advanced_ai/
├── __init__.py                  # Singletoni servisov
├── mlops_pipeline.py            # MLOps avtomatizacija
├── content_generation.py        # Generiranje vsebine
├── multimodal.py                # Izboljšan multimodalni AI
├── model_registry.py            # Verzioniranje modelov
├── automl.py                    # AutoML orkestracija
└── ab_testing.py                # A/B testiranje
```

---

## 🧪 Testiranje

Celovita testna pokritost z 31+ testnimi primeri.

### Zagon Testov

```bash
# Zagon vseh testov napredne AI
cd backend
pytest tests/test_mlops_pipeline.py -v
pytest tests/test_content_generation.py -v
pytest tests/test_ab_testing_service.py -v

# Zagon s pokritostjo
pytest tests/test_mlops_pipeline.py --cov=services.advanced_ai.mlops_pipeline
pytest tests/test_content_generation.py --cov=services.advanced_ai.content_generation
```

### Testna Pokritost

- **MLOps Pipeline**: 16 testnih primerov, ki pokrivajo vse faze življenjskega cikla
- **Generiranje Vsebine**: 15 testnih primerov, ki pokrivajo vse tipe generiranja
- **Multimodalni**: Integrirano z obstoječo testno zbirko

---

## 🔧 Konfiguracija

### Okoljske Spremenljivke

```bash
# Zahtevano za multimodalne funkcije
OPENAI_API_KEY=sk-...

# Neobvezna konfiguracija
OMNI_MINIMAL=0                   # Omogoči celoten nabor funkcij
PERF_SLOW_THRESHOLD_SEC=1.0      # Spremljanje zmogljivosti
```

---

## 📊 Premisleki o Zmogljivosti

### MLOps Pipeline

- **Čas Učenja**: Simulirano 45 sekund (nastavljivo)
- **Evalvacija**: Povprečno 3.5 sekunde
- **Uvajanje**: Povprečno 8 sekund
- **Priporočen Razpored**: Dnevno za produkcijske modele

### Generiranje Vsebine

- **Dokumentacija**: <1 sekunda za običajne delčke kode
- **Testni Podatki**: <2 sekundi za 1000 zapisov
- **Predlogi Funkcionalnosti**: <500ms za analizo
- **API Primeri**: <300ms za vse jezike

### Multimodalni AI

- **Analiza Slik**: 2-4 sekunde (OpenAI Vision API)
- **Generiranje Slik**: 10-30 sekund (DALL-E 3)
- **Transkripcija Zvoka**: ~1 sekunda na minuto (Whisper)
- **Besedilo v Govor**: ~2 sekundi za 100 besed

---

## 🔒 Varnost

- API ključi shranjeni v okoljskih spremenljivkah
- Vse končne točke zahtevajo avtentikacijo
- Omejitev klicanja uporabljena prek prehoda
- Validacija vhoda s Pydantic modeli
- Redakcija osebnih podatkov v dnevnikih

---

## 🚦 Primeri Uporabe

### Primer Python SDK

```python
import requests

API_BASE = "https://api.omni-enterprise.com"
API_KEY = "vaš-api-ključ"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Ustvarjanje MLOps pipeline
pipeline = requests.post(
    f"{API_BASE}/api/v1/advanced-ai/mlops/pipelines",
    json={
        "model_name": "napovedovalec_odhodov",
        "dataset_uri": "gs://moj-bucket/podatki.csv",
        "threshold": 0.88,
        "auto_deploy": True
    },
    headers=headers
).json()

print(f"Pipeline ustvarjen: {pipeline['id']}")

# Generiranje dokumentacije
docs = requests.post(
    f"{API_BASE}/api/v1/advanced-ai/content/documentation",
    json={
        "code_snippet": "def napovej(podatki): return model.predict(podatki)",
        "language": "python",
        "doc_format": "markdown"
    },
    headers=headers
).json()

print(docs["documentation"])

# Analiza slike
analiza = requests.post(
    f"{API_BASE}/api/v1/advanced-ai/multimodal/analyze",
    json={
        "image_url": "https://example.com/grafikon.png",
        "text": "Analiza prihodkov Q3"
    },
    headers=headers
).json()

print(f"Vpogledi: {analiza['insights']}")
```

---

## 📈 Spremljanje

Vsi servisi izpostavljajo metrike prek Prometheusa:

- `mlops_pipeline_runs_total`
- `mlops_pipeline_success_rate`
- `content_generation_requests_total`
- `multimodal_api_calls_total`

Ogled na: `/api/metrics`

---

## 🆘 Odpravljanje Težav

### Pogoste Težave

**Težava**: Klici OpenAI API ne uspejo
```
Rešitev: Preverite, ali je OPENAI_API_KEY pravilno nastavljen
```

**Težava**: Pipeline ne napreduje
```
Rešitev: Pokličite GET /mlops/pipelines/{id} za napredovanje simulacije stanja
```

**Težava**: Generiranje testnih podatkov je počasno
```
Rešitev: Zmanjšajte parameter count ali dodajte seed za predpomnenje
```

---

## 🎯 Prihodnje Izboljšave

Potencialne izboljšave za prihodnje različice:

1. **Učenje v Realnem Času**: Prenos metrik učenja med izvajanjem pipeline
2. **Razložljivost Modela**: Dodajte integracijo SHAP/LIME za interpretacijo modela
3. **Napredno Razporejanje**: Razporejanje podobno cron z uporabniškimi sprožilci
4. **Multi-Model Ensemble**: Samodejno ustvarjanje ensemble modelov
5. **Prilagojene Predloge Vsebine**: Uporabniško definirane predloge dokumentacije
6. **Analiza Videa**: Dodajte obdelavo videa v multimodalne zmožnosti

---

## 📝 Dnevnik Sprememb

### Različica 2.1.0 (2025-11-03)

- ✨ Dodan servis za avtomatizacijo MLOps Pipeline
- ✨ Dodan servis za generiranje vsebine
- ✨ Izboljšan multimodalni AI z OpenAI integracijami
- ✨ Dodano generiranje slik (DALL-E 3)
- ✨ Dodana pretvorba besedila v govor
- ✨ Dodanih 31+ celovitih testov
- 📝 Popolna API dokumentacija
- 🔧 Primeri konfiguracije in vodnik za odpravljanje težav
