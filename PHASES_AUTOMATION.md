# OMNI Platform – Avtomatsko kreiranje Phase Issues

Ta dokument opisuje, kako avtomatsko ustvariti 10 faznih Issues za profesionalni učni program ter kako so CI/Workflows organizirani. Namen je zagotoviti sledljivost dela in povezave na ključne referenčne Issues.

## Ključne reference
- Live pregled projekta: `#25` – https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/issues/25
- Strokovna revizija: `#26` – https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/issues/26

## Issue Template
- Template datoteka: `.github/ISSUE_TEMPLATE/phase-issue.yml`
- Config datoteka: `.github/ISSUE_TEMPLATE/config.yml`
- Ob ustvarjanju novega Phase issue uporabi dropdown za izbiro faze (1–10), opiši cilje, naloge in kriterije sprejema, ter dodaj povezave (npr. `#25`, `#26`, PR-ji).

## Avtomatska skripta
Skripta: `scripts/create_phase_issues.ps1`

Predpogoji:
- Nastavi GitHub token: `setx GITHUB_TOKEN <osebni_token>` ali v trenutni seji `set GITHUB_TOKEN=<osebni_token>`
- Token mora imeti pravice `repo`.

Primer uporabe:
- PowerShell:
  - `cd omni-enterprise-ultra-max`
  - `$env:GITHUB_TOKEN = "<token>"`
  - `./scripts/create_phase_issues.ps1 -Repo "robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform" -Labels @('dokumentacija','phase')`

Možnosti:
- `-DryRun` – izpiše, kaj bi se ustvarilo, brez dejanskega klica API.
- Skripta je idempotentna – preveri obstoječe naslove in preskoči podvajanja.

Ustvarjene faze:
1. Foundations & Architecture (4–6h)
2. Backend & AI/ML (50+ endpoints) (8–12h)
3. Gateway & API Security (6–8h)
4. Local Development Setup (2–3h)
5. Cloud Run Production (3–4h)
6. Monitoring & Grafana (4–6h)
7. Advanced AI/ML (10–14h)
8. Business Logic & Payments (8–10h)
9. Security & Compliance (6–8h)
10. Dashboards & CI/CD (10–12h)

## CI Workflow: Create Phase Issues
Če želiš ustvarjanje direktno prek GitHub Actions (brez lokalnega tokena), uporabi workflow:
- Datoteka: `.github/workflows/create-phase-issues.yml`
- Zagon: GitHub → Actions → "Create Phase Issues" → Run workflow
- Token: uporablja vgrajeni `GITHUB_TOKEN` in idempotentno preskoči obstoječe naslove.

## GitHub Actions CI
Repo že vključuje CI/workflows za ključne komponente:
- Backend: `.github/workflows/backend-ci.yml`, `ci-unit.yaml`, `ci-cd.yaml`
- Frontend: `.github/workflows/frontend-deploy.yml`, koraki v `ci-cd.yaml` (build/test)
- Gateway: `.github/workflows/deploy-gateway.yml`, `smoke-gateway.yml`

Priporočila:
- Za PR validacijo lahko uporabiš `ci-unit.yaml` in `backend-ci.yml` (za backend) ter dodane korake za frontend v `ci-cd.yaml`.
- Secrets/vars za Cloud Run naj bodo nastavljeni v `Repository Settings → Secrets and variables`.

## PR-ji in merge stabilnost
- Za stabilen merge PR-jev in preprečevanje napak uporabi `scripts/merge_prs.ps1` (če je na voljo) ali GitHub UI z omogočenimi CI status check.
- Priporočeno: vključi status checks (zahtevani) za glavne CI workflowe, da se PR lahko mergne le, ko testi uspešno pretečejo.

## Sprejemni kriteriji (Acceptance)
- Issues generirani in povezani na `#25` in `#26`.
- CI pipelines uspešno tečejo za backend/gateway/frontend (lint, test, build).
- Dokumentacija posodobljena (ta datoteka) in vidna v repozitoriju.

---

Če želiš, lahko razširimo skripto za avtomatsko odpiranje PR-jev s placeholder spremembami ali za sinhronizacijo dashboardov (Grafana) po fazah.