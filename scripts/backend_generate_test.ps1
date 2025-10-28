$ErrorActionPreference = 'Stop'

$base = 'http://localhost:8082'
$bodyObj = [ordered]@{
  model  = 'qwen3-coder:30b'
  prompt = 'Napiši en stavek v slovenščini.'
  stream = $false
}

$out = [ordered]@{}
$sw = [System.Diagnostics.Stopwatch]::StartNew()
try {
  $json = $bodyObj | ConvertTo-Json -Depth 6
  $resp = Invoke-WebRequest -Uri "$base/api/ollama/generate" -Method POST -ContentType 'application/json' -Body $json -TimeoutSec 300 -UseBasicParsing
  $sw.Stop()
  $out.Ok = $true
  $out.StatusCode = [int]$resp.StatusCode
  $out.DurationSec = [math]::Round($sw.Elapsed.TotalSeconds,1)
  try { $payload = $resp.Content | ConvertFrom-Json } catch { $payload = $null }
  if ($payload -ne $null) {
    $out.ResponsePreview = ($payload.response | Select-Object -First 1)
  } else {
    $out.RawContent = ($resp.Content.Substring(0, [Math]::Min(200, $resp.Content.Length)))
  }
} catch {
  $sw.Stop()
  $out.Ok = $false
  $out.Error = $_.Exception.Message
  if ($_.Exception.Response -ne $null) {
    $out.StatusCode = [int]$_.Exception.Response.StatusCode
    try {
      $stream = $_.Exception.Response.GetResponseStream()
      $reader = New-Object System.IO.StreamReader($stream)
      $text = $reader.ReadToEnd()
      $out.ResponseBody = $text.Substring(0, [Math]::Min(500, $text.Length))
    } catch {}
  }
}

$outPath = Join-Path $PSScriptRoot '_backend_generate_test.json'
$out | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $outPath
Write-Host "Wrote: $outPath"