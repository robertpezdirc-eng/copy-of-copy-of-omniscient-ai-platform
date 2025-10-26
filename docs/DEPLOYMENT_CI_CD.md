# CI/CD za Firebase Hosting (omni-search)

Ta dokument vas vodi skozi nastavitve CI/CD prek GitHub Actions za avtomatski deploy frontend aplikacije (omni-search) na Firebase Hosting.

## Predpogoji
- GitHub repozitorij povezan s projektom
- Firebase Hosting projekt: omni-platform-244c6
- Service Account JSON ključ z vlogo Firebase Admin ali zadostnimi pravicami za hosting deploy

## GitHub Secrets
V repozitoriju dodajte naslednje skrivnosti:

- FIREBASE_SERVICE_ACCOUNT: celoten JSON za Firebase Service Account ključ (kopirajte celotno vsebino .json datoteke)
- FIREBASE_PROJECT_ID: omni-platform-244c6

Pot: GitHub -> Settings -> Secrets and variables -> Actions -> New repository secret

## Workflow datoteke
V mapi `.github/workflows/` sta pripravljena workflowa:

- deploy-frontend.yml: Deploy na produkcijo (Firebase Hosting) ob push na `main`
- deploy-preview.yml: Deploy na Preview Channel za vsak PR (pull_request) – URL poteče po 7 dneh

Oba workflowa sta konfigurirana za subfolder `omni-search` preko `entryPoint: "omni-search"`.

## Spremenljivke okolja (Production)
V `omni-search/.env.production` je nastavljen:

- REACT_APP_BACKEND_URL=https://omni-unified-platform-661612368188.europe-west1.run.app

To zagotovi, da build uporablja pravi backend URL.

## Preverjanje CI/CD
1. Naredite majhno spremembo (npr. v README ali UI komponenti) in jo pushnite na `main`.
2. Odprite GitHub -> Actions in spremljajte job "Deploy Frontend to Firebase Hosting".
3. Po uspehu preverite Firebase Hosting URL (ali custom domeno, če jo nastavite).

Za PR:
1. Odprite PR z vašo spremembo.
2. V PR se pojavi komentar z Preview URL (Firebase Hosting channel), ki poteče po 7 dneh.

## Pogoste težave
- Manjkajoče secrets: prepričajte se, da sta oba (FIREBASE_SERVICE_ACCOUNT, FIREBASE_PROJECT_ID) pravilno dodana.
- NPM build napaka: preverite `omni-search/package.json` skripte in odvisnosti.
- CORS: ob custom domeni dodajte domeno v OMNI_FRONTEND_ORIGIN ali OMNI_FRONTEND_EXTRA_ORIGINS na backendu (Cloud Run) in redeploy.

## Varnost (opcijsko)
Namesto shranjevanja JSON ključev v GitHub Secrets razmislite o Workload Identity Federation (OIDC) za varnejše pooblastilo brez dolgoročnih ključev.