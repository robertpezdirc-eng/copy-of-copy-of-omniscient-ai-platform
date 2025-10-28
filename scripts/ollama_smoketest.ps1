$ErrorActionPreference = 'SilentlyContinue'

$result = [ordered]@{}
$model  = 'qwen3-coder:30b'

# Version and API basic checks
try { $result.Version = (& ollama --version) } catch { $result.Version = $null }
try {
  $ver = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 5 -Method GET
  $result.ApiReachable = $true
  $result.ApiVersion = $ver
} catch { $result.ApiReachable = $false }

# List models
try {
  $tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5 -Method GET
  $result.ApiModels = @($tags.models | ForEach-Object { $_.name })
} catch { $result.ApiModels = @() }
try {
  $out = & ollama list 2>$null
  $lines = $out -split "`r?`n" | Where-Object { $_ -and ($_ -notmatch '^NAME\s+ID\s+SIZE') }
  $result.CliModels = @($lines | ForEach-Object { ($_ -split '\s+')[0] })
} catch { $result.CliModels = @() }

# Generate test (non-streaming, long timeout)
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$ok = $false
$resp = $null
$err = $null
try {
  $body = @{ model=$model; prompt='Napiši besedo OK in ustavi.'; stream=$false; options=@{ num_predict=16; temperature=0.1 } } | ConvertTo-Json -Depth 5
  $gen = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/generate' -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 300
  $ok = $true
  $resp = $gen.response
} catch { $err = $_.Exception.Message }
$sw.Stop()

$result.Generate = [pscustomobject]@{
  Method='API /generate'; Model=$model; Ok=$ok; DurationSec=[math]::Round($sw.Elapsed.TotalSeconds,1);
  ResponsePreview = if($resp){ $resp.Substring(0, [Math]::Min(200, $resp.Length)) } else { $null };
  Error=$err
}

if(-not $ok){
  try {
    $sw.Restart()
    $cliOut = & ollama run $model 'Napiši samo OK' 2>$null
    $sw.Stop()
    $result.CliFallback = [pscustomobject]@{
      Method='CLI run'; Model=$model; Ok=$true; DurationSec=[math]::Round($sw.Elapsed.TotalSeconds,1);
      ResponsePreview = if($cliOut){ $cliOut.Substring(0, [Math]::Min(200, $cliOut.Length)) } else { $null }
    }
  } catch {
    $result.CliFallback = [pscustomobject]@{ Method='CLI run'; Model=$model; Ok=$false; Error=$_.Exception.Message }
  }
}

$outPath = Join-Path $PSScriptRoot '_ollama_smoketest.json'
$result | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $outPath
Write-Host "Wrote: $outPath"