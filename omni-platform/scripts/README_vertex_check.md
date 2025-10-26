# Vertex/Gemini Connectivity Check (PowerShell)

Ta skripta `scripts/vertex_connectivity_check.ps1` preveri:
- IAM vloge Cloud Run Service Account-a
- Zdravje Cloud Run storitve prek `GET /healthz`
- Testni klic na Vertex AI (Gemini) z minimalnim pozivom
- Zapiše rezultate v `vertex_connectivity_check.log`

## Zahteve
- Nameščen `gcloud` CLI in prijava (`gcloud auth login`)
- Nastavljen projekt (`gcloud config set project <PROJECT_ID>`) 
- Vključen Vertex AI API (`gcloud services enable aiplatform.googleapis.com`)

## Zagon
Primer z uporabo privzetih vrednosti (ProjectId se prebere iz `gcloud config`):

```powershell
# V ukazni vrstici v root mapi repoja
.\scripts\vertex_connectivity_check.ps1
```

Primer z eksplicitnimi parametri:

```powershell
.\scripts\vertex_connectivity_check.ps1 \ 
  -ProjectId "my-gcp-project" \ 
  -Region "us-central1" \ 
  -RunRegion "europe-west1" \ 
  -ServiceName "omni-exec-api" \ 
  -Model "gemini-1.5-flash-latest" \ 
  -HealthPath "/healthz"
```

Parametri:
- `-ProjectId`: GCP projekt (če ni podan, se vzame iz `gcloud config`)
- `-Region`: Vertex AI regija (npr. `us-central1`)
- `-RunRegion`: Cloud Run regija vaše storitve (npr. `europe-west1`)
- `-ServiceName`: Ime Cloud Run storitve (npr. `omni-exec-api`)
- `-Model`: Model za testni klic (npr. `gemini-1.5-flash-latest`)
- `-HealthPath`: pot do health endpointa (privzeto `/healthz`)

## Output
- Vsi koraki in rezultati se zapišejo v `vertex_connectivity_check.log` v trenutni mapi.
- Ob uspehu pri Gemini klicu se prikaže kratek tekstovni odgovor.

## Pogoste napake in rešitve
- Manjka vloga `roles/aiplatform.user` ali druge: dodaj vlogo SA:
  ```powershell
  gcloud projects add-iam-policy-binding <PROJECT_ID> \ 
    --member serviceAccount:<SERVICE_ACCOUNT_EMAIL> \ 
    --role roles/aiplatform.user
  ```
- `Access Token` ni na voljo: izvedi `gcloud auth login`.
- `Cloud Run URL` ni najden: preveri regijo `-RunRegion` in ime storitve `-ServiceName`.
- Napake GPU ali antivirus: te ne vplivajo na samo skripto, a lahko blokirajo lokalne zahteve; začasno onemogoči agresivne AV/EDR politike.

## Opombe
- Skripta bere Service Account iz konfiguracije storitve: `spec.template.spec.serviceAccountName`.
- Vertex AI endpoint se sestavi: `https://<Region>-aiplatform.googleapis.com/v1/projects/<ProjectId>/locations/<Region>/publishers/google/models/<Model>:generateContent`.
- Za hitro izolacijo težav lahko skripto zaženeš večkrat z različnimi `-RunRegion` in `-ServiceName`.