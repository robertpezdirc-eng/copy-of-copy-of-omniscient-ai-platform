# Generates alerts/alertmanager.generated.yml using environment variables, with safe defaults for local mocks.
# Usage: pwsh -File scripts/generate-alertmanager-config.ps1

$ErrorActionPreference = "Stop"

# Load .env into process environment if present
$envFilePath = Join-Path (Resolve-Path ".").Path ".env"
if (Test-Path $envFilePath) {
  Get-Content -Path $envFilePath | ForEach-Object {
    if ($_ -match '^\s*#') { return }
    if ($_ -match '^\s*$') { return }
    $kv = $_ -split '=', 2
    if ($kv.Length -eq 2) {
      $key = $kv[0].Trim()
      $val = $kv[1].Trim()
      Set-Item -Path Env:$key -Value $val
    }
  }
}

# Resolve environment with defaults
$slackUrl = if ($env:SLACK_WEBHOOK_URL) { $env:SLACK_WEBHOOK_URL } else { "http://mock-slack:9001/webhook" }
# Add optional dual Slack delivery flag
$dualSlack = if ($env:DUAL_SLACK_DELIVERY) { $env:DUAL_SLACK_DELIVERY.ToLower() } else { "false" }
# Optional Slack channel override; if not set, omit channel to use webhook's default
$slackChannel = $env:SLACK_CHANNEL
$smtpSmarthost = if ($env:SMTP_SMARTHOST) { $env:SMTP_SMARTHOST } else { "mailhog:1025" }
$smtpFrom = if ($env:SMTP_FROM) { $env:SMTP_FROM } else { "alertmanager@example.com" }
$smtpTo = if ($env:SMTP_TO) { $env:SMTP_TO } else { "ops@example.com" }
# Booleans in YAML should be barewords: true/false. If user sets string, normalize to lower.
$smtpRequireTLS = if ($env:SMTP_REQUIRE_TLS) { $env:SMTP_REQUIRE_TLS.ToLower() } else { "false" }
$smtpUser = $env:SMTP_USER
$smtpPass = $env:SMTP_PASS

# Build email receiver YAML with optional auth only if both user & pass provided
$emailConfig = @"
  - name: 'default'
    email_configs:
      - to: '$smtpTo'
        from: '$smtpFrom'
        smarthost: '$smtpSmarthost'
        require_tls: $smtpRequireTLS
"@
if ($smtpUser -and $smtpPass) {
  # Ensure proper newlines before auth fields
  $emailConfig += "`n        auth_username: '$smtpUser'`n        auth_password: '$smtpPass'`n"
}

# Optional enable/disable Slack
$slackEnabled = if ($env:SLACK_ENABLED) { $env:SLACK_ENABLED.ToLower() } else { "true" }
# Build slack receiver YAML
if ($slackEnabled -eq "true") {
  $slackConfig = @"
  - name: 'omni-notifications'
    slack_configs:
      - api_url: '$slackUrl'
"@
  # Ensure newline after api_url even when no channel override is provided
  $slackConfig += "`n"
  if ($slackChannel) { $slackConfig += "        channel: '$slackChannel'`n" }
  $slackConfig += @"
        send_resolved: true
        title: '{{ .CommonLabels.alertname }} ({{ .CommonLabels.severity }})'
        text: |
          *Alert:* {{ .CommonAnnotations.summary }}\n
          *Description:* {{ .CommonAnnotations.description }}\n
          *Service:* {{ .CommonLabels.service }}\n
          *Status:* {{ .Status }}\n
          *Labels:* {{ .CommonLabels }}\n
"@
  # Ensure newline separation before any subsequent receiver blocks
  $slackConfig += "`n"
  if ($dualSlack -eq "true") {
    $slackConfig += @"
  - name: 'omni-notifications-mock'
    slack_configs:
      - api_url: 'http://mock-slack:9001/webhook'
        channel: '#omni-notifications'
        send_resolved: true
        title: '{{ .CommonLabels.alertname }} ({{ .CommonLabels.severity }})'
        text: |
          *Alert:* {{ .CommonAnnotations.summary }}\n
          *Description:* {{ .CommonAnnotations.description }}\n
          *Service:* {{ .CommonLabels.service }}\n
          *Status:* {{ .Status }}\n
          *Labels:* {{ .CommonLabels }}\n
"@
    # Ensure newline separation at the end of mock receiver block
    $slackConfig += "`n"
  }
} else {
  $slackConfig = ""
}

# Build routes section with optional dual delivery route
if ($slackEnabled -eq "true") {
  $routes = @"
    - match:
        severity: 'critical'
      receiver: 'omni-notifications'
      continue: true

"@
  if ($dualSlack -eq "true") {
    $routes += @"
    - match:
        severity: 'critical'
      receiver: 'omni-notifications-mock'
      continue: true

"@
  }
  # Always deliver critical to email as well
  $routes += @"
    - match:
        severity: 'critical'
      receiver: 'default'

"@
} else {
  $routes = @"
    - match:
        severity: 'critical'
      receiver: 'default'

"@
}
# Always include warning route to default
$routes += @"
    - match:
        severity: 'warning'
      receiver: 'default'
"@
# Ensure newline separation before next route
$routes += "`n"
# Conditionally add service-specific route based on Slack enablement
if ($slackEnabled -eq "true") {
  $routes += @"
    - match:
        service: 'omni-unified'
      receiver: 'omni-notifications'
"@
} else {
  $routes += @"
    - match:
        service: 'omni-unified'
      receiver: 'default'
"@
}

# Combine full Alertmanager config
$yaml = @"
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'service', 'instance']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 2h
  receiver: 'default'
  routes:
$routes

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance', 'job']

receivers:
$emailConfig
$slackConfig
"@

$targetPath = Join-Path -Path (Resolve-Path "alerts").Path -ChildPath "alertmanager.generated.yml"

# Write file
[System.IO.File]::WriteAllText($targetPath, $yaml, [System.Text.Encoding]::UTF8)

Write-Host "Generated: $targetPath"
Write-Host "  Slack URL: $slackUrl"
Write-Host "  Slack enabled: $slackEnabled"
Write-Host "  SMTP: smarthost=$smtpSmarthost, from=$smtpFrom, to=$smtpTo, require_tls=$smtpRequireTLS" 
Write-Host "  Dual Slack delivery: $dualSlack" 
if ($smtpUser -and $smtpPass) {
  Write-Host "  SMTP auth: user provided"
} else {
  Write-Host "  SMTP auth: none"
}