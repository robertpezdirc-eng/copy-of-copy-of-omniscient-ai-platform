$ErrorActionPreference = 'SilentlyContinue'

$base = 'http://localhost:8082'
$res = [ordered]@{}

try { $h = Invoke-RestMethod -Uri "$base/api/health" -TimeoutSec 4 -Method GET; $res.ApiHealth = $h } catch { $res.ApiHealth = $null }
try { $o = Invoke-RestMethod -Uri "$base/api/ollama/health" -TimeoutSec 4 -Method GET; $res.OllamaHealth = $o } catch { $res.OllamaHealth = $null }
try { $m = Invoke-RestMethod -Uri "$base/api/ollama/models" -TimeoutSec 4 -Method GET; $res.Models = $m } catch { $res.Models = $null }

$outPath = Join-Path $PSScriptRoot '_backend_check.json'
$res | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $outPath
Write-Host "Wrote: $outPath"