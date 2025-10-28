Param(
    [switch]$SkipPull,
    [string]$TestImage = 'alpine:3.19',
    [int]$TimeoutSec = 60
)

$ErrorActionPreference = 'Stop'

function New-StepResult {
    param(
        [string]$Name,
        [bool]$Success,
        [string]$Message,
        [TimeSpan]$Duration
    )
    [PSCustomObject]@{
        Step      = $Name
        Success   = $Success
        Duration  = ('{0:n1}s' -f $Duration.TotalSeconds)
        Message   = $Message
    }
}

function Invoke-WithTimer {
    param(
        [string]$Name,
        [scriptblock]$Action
    )
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $msg = & $Action
        $sw.Stop()
        return New-StepResult -Name $Name -Success $true -Message $msg -Duration $sw.Elapsed
    }
    catch {
        $sw.Stop()
        return New-StepResult -Name $Name -Success $false -Message ($_.Exception.Message) -Duration $sw.Elapsed
    }
}

function Write-StepOutcome {
    param([PSCustomObject]$r)
    if ($r.Success) {
        Write-Host ("[OK]  {0} ({1}) - {2}" -f $r.Step, $r.Duration, $r.Message) -ForegroundColor Green
    } else {
        Write-Host ("[ERR] {0} ({1}) - {2}" -f $r.Step, $r.Duration, $r.Message) -ForegroundColor Red
    }
}

function Test-ExecExists {
    Param([string]$Cmd)
    Get-Command $Cmd -ErrorAction Stop | Out-Null
    return $true
}

function Invoke-Docker {
    param([string[]]$Args)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'docker'
    $psi.Arguments = ($Args -join ' ')
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $p = [System.Diagnostics.Process]::Start($psi)
    if (-not $p.WaitForExit($TimeoutSec * 1000)) {
        $p.Kill()
        throw "Timeout after $TimeoutSec s: docker $($Args -join ' ')"
    }
    $out = $p.StandardOutput.ReadToEnd().Trim()
    $err = $p.StandardError.ReadToEnd().Trim()
    if ($p.ExitCode -ne 0) {
        $msg = if ($err) { $err } else { $out }
        throw $msg
    }
    return $out
}

$results = New-Object System.Collections.Generic.List[object]

# 1) CLI prisotnost
$results.Add((Invoke-WithTimer -Name 'docker CLI prisoten' -Action {
    Test-ExecExists docker | Out-Null
    'docker OK'
}))

# 2) Docker info
$results.Add((Invoke-WithTimer -Name 'docker info' -Action {
    $o = Invoke-Docker @('info')
    if ($o -match 'Server Version') { 'daemon responsive' } else { 'daemon responded' }
}))

# 3) docker ps
$results.Add((Invoke-WithTimer -Name 'docker ps' -Action {
    Invoke-Docker @('ps', '--format', 'table {{.ID}}\t{{.Names}}\t{{.Status}}') | Out-Null
    'ps OK'
}))

# 4) docker pull (neobvezno)
if (-not $SkipPull) {
    $results.Add((Invoke-WithTimer -Name "docker pull $TestImage" -Action {
        $o = Invoke-Docker @('pull', $TestImage)
        if ($o -match 'Downloaded|Image is up to date') { 'pull OK' } else { $o }
    }))
} else {
    $results.Add((New-StepResult -Name "docker pull $TestImage (preskočeno)" -Success $true -Message 'SkipPull' -Duration ([TimeSpan]::Zero)))
}

# 5) docker run echo ok
$results.Add((Invoke-WithTimer -Name 'docker run echo' -Action {
    $o = Invoke-Docker @('run', '--rm', $TestImage, 'echo', 'ok')
    if ($o.Trim() -eq 'ok') { 'run OK' } else { "unexpected output: $o" }
}))

# 6) docker compose ls (če je na voljo)
$results.Add((Invoke-WithTimer -Name 'docker compose ls' -Action {
    try {
        Invoke-Docker @('compose', 'ls') | Out-Null
        'compose OK'
    } catch {
        # Starejše verzije lahko nimajo compose, ne štej kot fatalno
        'compose not available'
    }
}))

# Izpis in izhodna koda
$allOk = $true
foreach ($r in $results) {
    Write-StepOutcome $r
    if (-not $r.Success) { $allOk = $false }
}

if ($allOk) {
    Write-Host "\nDocker OK" -ForegroundColor Green
    exit 0
} else {
    Write-Host "\nDocker NI OK" -ForegroundColor Red
    exit 1
}