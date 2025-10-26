# Fetch and display latest Mailhog message details in a PowerShell-friendly way
# Usage: pwsh -File scripts/get-mailhog-latest.ps1

$ErrorActionPreference = "Stop"

$apiUrl = "http://localhost:8025/api/v2/messages"

try {
  $resp = Invoke-WebRequest -UseBasicParsing -Uri $apiUrl -Method Get
  $json = $resp.Content | ConvertFrom-Json

  Write-Host ("Total messages: " + $json.total)

  if ($json.items.Length -eq 0) {
    Write-Host "No messages found."
    exit 0
  }

  # Mailhog returns items sorted by time descending, so [0] is the most recent
  $latest = $json.items[0]

  $subject = $latest.Content.Headers.Subject
  $from = $latest.Content.Headers.From
  $to = $latest.Content.Headers.To

  Write-Host ("Subject: " + $subject)
  Write-Host ("From: " + $from)
  Write-Host ("To: " + $to)

  # Show short preview of HTML body if present
  if ($latest.Content.Body) {
    $body = $latest.Content.Body
    $preview = if ($body.Length -gt 300) { $body.Substring(0,300) + "..." } else { $body }
    Write-Host "Body preview:"
    Write-Host $preview
  } else {
    Write-Host "No body content present."
  }
}
catch {
  Write-Error $_
  exit 1
}