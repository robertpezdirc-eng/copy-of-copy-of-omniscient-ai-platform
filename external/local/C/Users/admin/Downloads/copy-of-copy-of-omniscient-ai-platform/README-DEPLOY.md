# Production Deploy Pack (Final Polish)

Ta paket poenoti regije, pripravi Artifact Registry, nastavi minimalne instance in concurrency, preklopi na Secret Manager ter preveri health endpoint. Vse operacije so varne: ukazi preskakujejo manjkajoče storitve/datoteke in ne prekinjajo obstoječe produkcije.

## Prerequisites
- `gcloud` prijavljen v projekt `refined-graph-471712-n9` (ali nastavljen `PROJECT_ID`)
- IAM pravice: Cloud Run Admin, Cloud Build Editor, Artifact Registry Admin, Secret Manager Admin
- Lokalno: `bash` (za `deploy-fix.sh`) in `curl`

## 1) Poenoti regijo
```bash
gcloud config set run/region europe-west1
# Cloud Build nima globalne config lastnosti za lokacijo; v ukazih uporabi --region.
```

## 2) Artifact Registry (urejeno produkcijsko skladišče)
```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
# Ustvari repo, če ne obstaja
gcloud artifacts repositories create omni \
  --repository-format=docker \
  --location=europe-west1 \
  --description="Omni platform images"
```

- Slike v Cloud Build zapiši kot:
```
europe-west1-docker.pkg.dev/${PROJECT_ID}/omni/<service>:${SHORT_SHA}
```
- Če imaš `cloudbuild.missing-services.yaml`, zamenjaj `gcr.io/${PROJECT_ID}` z `europe-west1-docker.pkg.dev/${PROJECT_ID}/omni`.

## 3) Min instances in concurrency
```bash
gcloud run services update omni-api-gateway --min-instances 1 --concurrency 80 --region europe-west1
gcloud run services update omni-singularity --min-instances 1 --concurrency 40 --region europe-west1
```
Opomba: Ukazi uspešno delujejo le, če storitve obstajajo v `europe-west1`.

## 4) Secret Manager namesto `.env`
```bash
# Ustvari skrivnost
printf 'YOUR_SECRET_VALUE' | gcloud secrets create OPENAI_API_KEY --data-file=- --replication-policy=automatic

# Poveži s storitvijo (primer omni-api)
gcloud run services update omni-api \
  --set-secrets "OPENAI_API_KEY=projects/${PROJECT_ID}/secrets/OPENAI_API_KEY:latest" \
  --region europe-west1
```
- `.env` je že v `.gitignore` in `.dockerignore`. Hranjenje občutljivih vrednosti v repo ni priporočeno.

## 5) Health endpoint preverba
```bash
curl -I https://omni-api-gateway-guzjyv6gfa-ew.a.run.app/healthz
```
- Če ne vrne `200`, dodaj handler:
  - FastAPI
    ```python
    @app.get("/healthz")
    def health():
        return {"status": "ok"}
    ```
  - Express
    ```js
    app.get('/healthz', (req, res) => res.status(200).json({status: 'ok'}));
    ```

## 6) (Opcijsko) Domain mapping
```bash
gcloud run domain-mappings create \
  --region europe-west1 \
  --service omni-api-gateway \
  --domain api.omni-platform.ai \
  --certificate-mode managed
```
- DNS CNAME na Cloud Run domeno se nastavi samodejno po kreaciji.

## 7) CI/CD nadgradnje (opcijsko)
- Test korak v `.github/workflows/deploy-cloudrun-prod.yml` (npr. `pytest` ali `curl /healthz`)
- Rollback, če health faila po deployu:
```bash
gcloud run services update omni-api-gateway --image <previous_image> --region europe-west1
```
- Verzije:
```bash
gcloud run deploy omni-api-gateway --revision-suffix v1-0-3
```

## 8) Hitri zagon
```bash
# Zaženi vse iz enega mesta
bash ./deploy-fix.sh
```
Skripta:
- Poenoti regijo in konfigurira AR docker auth
- Ustvari AR repozitorij `omni` (če ne obstaja)
- Poskusi zamenjati GCR -> AR referenco v `cloudbuild.missing-services.yaml` (če obstaja)
- Posodobi min-instances in concurrency za ključne storitve (če obstajajo)
- Ustvari/poveže `OPENAI_API_KEY` (če podan) in preveri `/healthz`
- Izpiše primer `domain-mappings` ukaza

## 9) Opombe
- Če imaš Cloud Build triggerje, nastavi lokacijo `--region europe-west1` v triggerjih.
- Za migracijo GCR -> AR v produkciji poskrbi, da Cloud Run deploy referencira novo sliko iz AR.