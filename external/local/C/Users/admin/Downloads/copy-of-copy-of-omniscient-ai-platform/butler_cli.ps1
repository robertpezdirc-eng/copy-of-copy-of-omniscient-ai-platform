param(
  [Parameter(Mandatory=$true)][string]$Message,
  [switch]$Confirm,
  [string]$ServerUrl = "http://localhost:5000"
)

Write-Host "Butler: '$Message' (Confirm=$($Confirm.IsPresent))" -ForegroundColor Cyan

$bodyObj = @{ message = $Message; confirm = [bool]$Confirm.IsPresent }
$json = $bodyObj | ConvertTo-Json -Depth 5

try {
  $res = Invoke-RestMethod -Uri "$ServerUrl/api/butler" -Method Post -ContentType "application/json" -Body $json
  Write-Host "Odgovor prejet" -ForegroundColor Green
  if ($res.plan) {
    Write-Host "Plan:" -ForegroundColor Yellow
    $res.plan | ConvertTo-Json -Depth 8
  }
  if ($res.results) {
    Write-Host "Rezultati:" -ForegroundColor Yellow
    $res.results | ConvertTo-Json -Depth 8
  }
} catch {
  Write-Host "Napaka: $($_.Exception.Message)" -ForegroundColor Red
  if ($_.ErrorDetails -and $_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
}

Write-Host "Done." -ForegroundColor Cyan