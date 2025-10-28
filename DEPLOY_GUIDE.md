# Deploy Guide - Avtomatski CI/CD z LangGraph

## Pregled

`avto_builder.py` zdaj podpira avtomatski deploy na različne platforme z inteligentnim zaznavanjem konfiguracije.

## Podprte Platforme

### 1. Google Cloud Run
**Zaznavanje**: `cloudbuild.yaml` + `GOOGLE_CLOUD_PROJECT` okoljska spremenljivka

**Okoljske spremenljivke**:
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="europe-west1"  # opcijsko, privzeto europe-west1
export CLOUD_RUN_SERVICE="my-llm-app"      # opcijsko, privzeto my-llm-app
```

**Deploy proces**:
1. `docker tag my-llm-app-prod:latest europe-west1-docker.pkg.dev/PROJECT/omni-registry/SERVICE:latest`
2. `docker push europe-west1-docker.pkg.dev/PROJECT/omni-registry/SERVICE:latest`
3. `gcloud run deploy SERVICE --image ... --region REGION --port 8080 --memory 1Gi`

### 2. Render.com
**Zaznavanje**: `render.yaml` datoteka

**Okoljske spremenljivke**:
```bash
export DOCKER_HUB_USERNAME="your-dockerhub-user"
export RENDER_SERVICE="my-llm-app"  # opcijsko, privzeto my-llm-app
```

**Deploy proces**:
1. `docker tag my-llm-app-prod:latest USERNAME/SERVICE:latest`
2. `docker push USERNAME/SERVICE:latest`
3. Render avtomatsko zazna novo sliko (če je webhook konfiguriran)

### 3. Railway
**Zaznavanje**: `railway.json` datoteka ali `RAILWAY_TOKEN` okoljska spremenljivka

**Okoljske spremenljivke**:
```bash
export RAILWAY_TOKEN="your-railway-token"
```

**Deploy proces**:
1. `railway login --browserless`
2. `railway up --detach`

### 4. Docker Hub (generični)
**Zaznavanje**: `DOCKER_HUB_USERNAME` okoljska spremenljivka

**Deploy proces**: Enak kot Render (push na Docker Hub)

### 5. Lokalni Deploy
**Zaznavanje**: Privzeto, če nobena druga platforma ni zaznana

**Deploy proces**: Preveri, da Docker slika obstaja lokalno

## Uporaba

### Avtomatski Deploy z LangGraph
```bash
# Nastavi avtomatsko odobritev
export AUTO_APPROVE_PROD=true

# Zaženi CI/CD potek
python avto_builder.py
```

### Ročni Deploy Test
```bash
# Brez avtomatske odobritve (interaktivno)
python avto_builder.py
```

## Potek CI/CD

1. **Build**: Pripravi minimalni build kontekst in zgradi Docker sliko
2. **Approval**: Zahteva človeško odobritev (ali avtomatsko z `AUTO_APPROVE_PROD=true`)
3. **Deploy**: Zazna platformo in izvede ustrezen deploy
4. **Monitor**: Preveri status deploy-a in dostopnost

## Minimalni Build Kontekst

Sistem avtomatsko ustvari `build_context/` mapo z:
- `backend/` - kopija backend kode
- `Dockerfile` - kopija `Dockerfile.backend`

To prepreči "Access is denied" napake na Windows sistemih.

## Varnostne Funkcije

- Človeška odobritev pred produkcijo
- Varnostno preverjanje ukazov
- Timeout za ukaze (180s privzeto)
- UTF-8 encoding za stabilne izpise

## Troubleshooting

### "Access is denied" med Docker build
✅ **Rešeno**: Sistem uporablja minimalni build kontekst

### Unicode napake v izpisih
✅ **Rešeno**: UTF-8 encoding z `errors='replace'`

### Deploy ne deluje
1. Preveri okoljske spremenljivke za izbrano platformo
2. Preveri, da je Docker slika zgrajena: `docker images my-llm-app-prod:latest`
3. Preveri konfiguracijske datoteke (`render.yaml`, `cloudbuild.yaml`)

### Interaktivna odobritev ne deluje
Nastavi `AUTO_APPROVE_PROD=true` za avtomatsko odobritev

## Primer Kompletnega Deploy-a

```bash
# Cloud Run deploy
export GOOGLE_CLOUD_PROJECT="my-project"
export AUTO_APPROVE_PROD=true
python avto_builder.py

# Render deploy
export DOCKER_HUB_USERNAME="myuser"
export AUTO_APPROVE_PROD=true
python avto_builder.py

# Lokalni test
export AUTO_APPROVE_PROD=true
python avto_builder.py
```

## Naslednji Koraki

- Dodaj health check URL-je za monitoring
- Integriraj z Slack/Discord obvestili
- Dodaj rollback funkcionalnost
- Implementiraj blue-green deployment