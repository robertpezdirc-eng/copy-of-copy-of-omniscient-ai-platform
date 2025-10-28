$ErrorActionPreference = 'SilentlyContinue'

$model = 'qwen3-coder:30b'
$result = [ordered]@{}

try { $ver = (& ollama --version) } catch { $ver = $null }
$result.Version = $ver

try { $apiVer = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 5 -Method GET; $result.ApiReachable=$true; $result.ApiVersion=$apiVer } catch { $result.ApiReachable=$false }

# Build chat body
$messages = @(
  @{ role='system'; content='You are a concise assistant. Respond briefly.' },
  @{ role='user'; content='Napiši samo besedo OK.' }
)
$body = @{ model=$model; stream=$false; messages=$messages } | ConvertTo-Json -Depth 6

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$ok=$false; $resp=$null; $err=$null
try {
  $chat = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/chat' -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 300
  $ok=$true
  $resp = $chat.message.content
} catch { $err = $_.Exception.Message }
$sw.Stop()

$result.Chat = [pscustomobject]@{
  Method='API /chat'; Model=$model; Ok=$ok; DurationSec=[math]::Round($sw.Elapsed.TotalSeconds,1);
  ResponsePreview = if($resp){ $resp.Substring(0, [Math]::Min(120, $resp.Length)) } else { $null };
  Error=$err
}

$outPath = Join-Path $PSScriptRoot '_ollama_chat_smoketest.json'
$result | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $outPath
Write-Host "Wrote: $outPath"