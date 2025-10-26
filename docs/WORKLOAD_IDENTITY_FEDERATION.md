# Workload Identity Federation (OIDC) za GitHub Actions

Ta dokument opisuje, kako nastaviti varno avtentikacijo za CI/CD brez JSON ključev za Firebase Hosting deploye. Uporabimo Google Cloud Workload Identity Federation (OIDC) in kratkožive poverilnice.

## Predpogoji
- Project ID: refined-graph-471712-n9
- Project Number: 661612368188
- GitHub repo: OWNER/REPO (npr. robertpezdirc/omniscient-ai-platform)

## Hitra nastavitev prek PowerShell skripte
Zaženite skripto (primer z dvema repozitorijema in cross-project pravicami na Firebase projektu):

```powershell
./scripts/gcp_wif_setup.ps1 `
  -ProjectId refined-graph-471712-n9 `
  -ProjectNumber 661612368188 `
  -OwnerRepos @("robertpezdirc/omniscient-ai-platform","robertpezdirc-eng/omni") `
  -PoolId github `
  -ProviderId github `
  -ServiceAccountEmail "ci-deployer@refined-graph-471712-n9.iam.gserviceaccount.com" `
  -FirebaseProjectId "omni-platform-244c6"
```

Skripta izvede:
1) Ustvari Workload Identity Pool in OIDC Provider za GitHub Actions (v projektu refined-graph-471712-n9)
2) Ustvari (ali preveri) CI Deployer Service Account
3) Dodeli minimalne vloge na izvorni (OIDC) projekt in na ciljnega Firebase projekt (omni-platform-244c6) za deploy
4) Doda WorkloadIdentityUser binding za vse podane GitHub repozitorije, da lahko Actions impersonira SA

## GitHub Actions workflow (že dodan)
- .github/workflows/deploy-frontend-oidc.yml
- .github/workflows/deploy-preview-oidc.yml

Oba workflowa:
- Uporabljata google-github-actions/auth@v2 z OIDC
- Izvozita GOOGLE_APPLICATION_CREDENTIALS do kratkoživih poverilnic
- Gradita in deployata z `firebase-tools` (ADC), brez JSON ključev

## Verifikacija
1) Naredite majhno spremembo v `omni-search/src/App.jsx` (npr. sprememba teksta).
2) Push na `main` -> pričakovan samodejni deploy na Firebase Hosting prek OIDC.
3) Odprite PR -> pričakovan samodejni deploy v preview channel (pr-<PR_NUMBER>).

Če deploy faila zaradi avtentikacije:
- Preverite, da je WIF binding upošteval točen `OWNER/REPO`.
- Preverite vloge na service accountu.
- Začasni fallback: uporabite obstoječi workflow z `FIREBASE_SERVICE_ACCOUNT` JSON; nato znova poskusite z OIDC.

## Varnostne prednosti
- Ni JSON ključa v GitHub Secrets.
- Poverilnice so kratkožive in omejene na specifičen repo/workflow.
- Manjša površina za napade in boljši audit.