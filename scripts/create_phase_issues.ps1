<#
 .SYNOPSIS
  Avtomatsko kreiranje 10 Phase issues v GitHub repozitoriju.

 .DESCRIPTION
  Ustvari standardizirane Phase issues (1–10) za OMNI platformo in jih označi
  z ustreznimi labelami. Skripta uporablja GitHub REST API v PowerShellu.

 .REQUIREMENTS
  - PowerShell 5+
  - Okoljska spremenljivka `GITHUB_TOKEN` (osebni token z repo scope)

 .USAGE
  PS> $env:GITHUB_TOKEN = "<token>"
  PS> ./scripts/create_phase_issues.ps1 -Repo "robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform" -Labels @('dokumentacija','phase') -DryRun:$false

 .NOTES
  - Referenčni issues: #25 in #26
  - Skripta idempotentno preverja obstoječe naslove in se izogne podvojenim kreacijam.
#>

param(
  [Parameter(Mandatory=$true)]
  [string]$Repo,

  [string[]]$Labels = @('dokumentacija','phase'),

  [switch]$DryRun
)

function Ensure-GitHubToken {
  if (-not $env:GITHUB_TOKEN) {
    throw "GITHUB_TOKEN ni nastavljen. Nastavi ga: `$env:GITHUB_TOKEN = '<token>'"
  }
}

function Invoke-GitHubRequest {
  param(
    [string]$Method,
    [string]$Uri,
    [object]$Body = $null
  )
  $headers = @{
    Authorization = "Bearer $($env:GITHUB_TOKEN)"
    Accept        = "application/vnd.github+json"
    "User-Agent"  = "omni-phase-automation"
  }
  if ($Body) {
    $json = $Body | ConvertTo-Json -Depth 10
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers -ContentType 'application/json' -Body $json
  } else {
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers
  }
}

function Get-ExistingIssues {
  param([string]$Repo)
  $issues = @()
  $page = 1
  do {
    $uri = "https://api.github.com/repos/$Repo/issues?state=open&per_page=100&page=$page"
    $batch = Invoke-GitHubRequest -Method GET -Uri $uri
    if ($batch) { $issues += $batch }
    $page += 1
  } while ($batch -and $batch.Count -gt 0 -and $issues.Count -lt 1000)
  return $issues
}

function New-PhaseIssue {
  param(
    [string]$Repo,
    [int]$PhaseNumber,
    [string]$PhaseTitle,
    [string[]]$Labels
  )

  $title = "Phase $PhaseNumber: $PhaseTitle"

  $body = @"
## ✨ Kompletan Learning Program – Phase $PhaseNumber

Referenčni issues: #25, #26

Opis:
- Ta issue pokriva fazo "$PhaseTitle" iz profesionalnega 10-faznega učnega programa.

Naloge:
- [ ] Preglej specifikacije in obstoječo kodo v repozitoriju
- [ ] Pripravi načrt izvedbe in kriterije sprejema
- [ ] Implementiraj spremembe v ustreznih modulih (backend/gateway/frontend)
- [ ] Posodobi dokumentacijo (README, Guides)
- [ ] Dodaj povezave na PR-je, teste in dashboarde

Kriteriji sprejema:
- Build in testi pretečejo (CI)
- Dokumentacija posodobljena in sklicuje #25 ter #26
- Vse naloge označene kot dokončane

"@

  $payload = @{ title = $title; body = $body; labels = $Labels }

  if ($DryRun) {
    Write-Host "[DRY-RUN] Ustvaril bi issue: '$title' z labelami: $($Labels -join ', ')" -ForegroundColor Yellow
    return $null
  }

  $uri = "https://api.github.com/repos/$Repo/issues"
  try {
    $result = Invoke-GitHubRequest -Method POST -Uri $uri -Body $payload
    Write-Host "[OK] Ustvarjen issue: $($result.html_url)" -ForegroundColor Green
    return $result
  } catch {
    Write-Host "[ERROR] Neuspeh pri ustvarjanju '$title': $($_.Exception.Message)" -ForegroundColor Red
    throw
  }
}

if (-not $DryRun) {
  Ensure-GitHubToken
}

$phases = @(
  @{ n=1;  t='Foundations & Architecture (4-6h)' }
  @{ n=2;  t='Backend & AI/ML (50+ endpoints) (8-12h)' }
  @{ n=3;  t='Gateway & API Security (6-8h)' }
  @{ n=4;  t='Local Development Setup (2-3h)' }
  @{ n=5;  t='Cloud Run Production (3-4h)' }
  @{ n=6;  t='Monitoring & Grafana (4-6h)' }
  @{ n=7;  t='Advanced AI/ML (10-14h)' }
  @{ n=8;  t='Business Logic & Payments (8-10h)' }
  @{ n=9;  t='Security & Compliance (6-8h)' }
  @{ n=10; t='Dashboards & CI/CD (10-12h)' }
)

Write-Host "Repo: $Repo" -ForegroundColor Cyan
Write-Host "Labels: $($Labels -join ', ')" -ForegroundColor Cyan
Write-Host "DryRun: $DryRun" -ForegroundColor Cyan

# Prepreči podvajanja po naslovu
if ($DryRun) {
  $existingTitles = @()
} else {
  $existing = Get-ExistingIssues -Repo $Repo
  $existingTitles = @($existing | ForEach-Object { $_.title })
}

foreach ($p in $phases) {
  $candidateTitle = "Phase $($p.n): $($p.t)"
  if ($existingTitles -contains $candidateTitle) {
    Write-Host "[SKIP] Issue že obstaja: $candidateTitle" -ForegroundColor DarkYellow
    continue
  }
  New-PhaseIssue -Repo $Repo -PhaseNumber $p.n -PhaseTitle $p.t -Labels $Labels | Out-Null
}

Write-Host "✅ Končano. Faze so ustvarjene oziroma preverjene." -ForegroundColor Green