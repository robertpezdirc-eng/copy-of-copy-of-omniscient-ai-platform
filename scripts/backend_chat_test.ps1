$ErrorActionPreference = 'Stop'

$base = 'http://localhost:8082'
$bodyObj = [ordered]@{
  model   = 'qwen3-coder:30b'
  stream  = $false
  messages = @(
    @{ role = 'user'; content = 'Zapiši eno kratko slovensko poved.' }
  )
}

$out = [ordered]@{}
try {
  $json = $bodyObj | ConvertTo-Json -Depth 6
  $resp = Invoke-WebRequest -Uri "$base/api/ollama/chat" -Method POST -ContentType 'application/json' -Body $json -TimeoutSec 300 -UseBasicParsing
  $out.Ok = $true
  $out.StatusCode = [int]$resp.StatusCode
  try { $payload = $resp.Content | ConvertFrom-Json } catch { $payload = $null }
  if ($payload -ne $null) {
    $out.ResponsePreview = ($payload.message.content | Select-Object -First 1)
  } else {
    $out.RawContent = ($resp.Content.Substring(0, [Math]::Min(200, $resp.Content.Length)))
  }
} catch {
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

$outPath = Join-Path $PSScriptRoot '_backend_chat_test.json'
$out | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $outPath
Write-Host "Wrote: $outPath"