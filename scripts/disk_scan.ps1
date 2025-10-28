$ErrorActionPreference = 'SilentlyContinue'

function Get-SizeBytes([string]$Path){
  try {
    if(Test-Path -LiteralPath $Path){
      $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
      if($item.PSIsContainer){
        return (Get-ChildItem -LiteralPath $Path -Force -Recurse -ErrorAction SilentlyContinue | Measure-Object -Sum Length).Sum
      } else {
        return $item.Length
      }
    }
  } catch {}
  return 0
}

$report = [ordered]@{}

# Drive summary
$drive = Get-PSDrive -Name C -ErrorAction SilentlyContinue
if($drive){
  $report.Drive = [pscustomobject]@{
    UsedGB  = [math]::Round(($drive.Used/1GB),2)
    FreeGB  = [math]::Round(($drive.Free/1GB),2)
    TotalGB = [math]::Round((($drive.Used+$drive.Free)/1GB),2)
  }
}

# Key system consumers
$report.RecycleBinGB             = [math]::Round((Get-SizeBytes 'C:\$Recycle.Bin')/1GB,2)
$report.WindowsInstallerGB       = [math]::Round((Get-SizeBytes 'C:\Windows\Installer')/1GB,2)
$report.WindowsUpdateDownloadsGB = [math]::Round((Get-SizeBytes 'C:\Windows\SoftwareDistribution\Download')/1GB,2)
$report.ProgramDataGB            = [math]::Round((Get-SizeBytes 'C:\ProgramData')/1GB,2)
$report.AdminTempGB              = [math]::Round((Get-SizeBytes (Join-Path $env:LOCALAPPDATA 'Temp'))/1GB,2)

# Big system files
if(Test-Path 'C:\hiberfil.sys'){ $report.HiberfilGB = [math]::Round(((Get-Item 'C:\hiberfil.sys').Length/1GB),2) }
if(Test-Path 'C:\pagefile.sys'){ $report.PagefileGB = [math]::Round(((Get-Item 'C:\pagefile.sys').Length/1GB),2) }

# Docker / WSL virtual disks (VHDX)
$vhdx = @()
$vhdx += Get-ChildItem "$env:LOCALAPPDATA\Docker\wsl" -Recurse -Filter *.vhdx -ErrorAction SilentlyContinue
$vhdx += Get-ChildItem "$env:LOCALAPPDATA\Packages" -Recurse -Filter ext4.vhdx -ErrorAction SilentlyContinue
$vhdx += Get-ChildItem 'C:\ProgramData\Docker' -Recurse -Filter *.vhdx -ErrorAction SilentlyContinue
$vhdx += Get-ChildItem 'C:\Users\admin' -Recurse -Filter *.vhdx -ErrorAction SilentlyContinue -Depth 4
$report.VHDX = $vhdx | Sort-Object Length -Descending | Select-Object -First 10 | ForEach-Object {
  [pscustomobject]@{ Path=$_.FullName; SizeGB=[math]::Round(($_.Length/1GB),2) }
}

# ProgramData top offenders (top 10 subfolders)
if(Test-Path 'C:\ProgramData'){
  $pd = Get-ChildItem 'C:\ProgramData' -Force -ErrorAction SilentlyContinue | Where-Object { $_.PSIsContainer }
  $report.ProgramDataTop = @(
    foreach($d in $pd){
      try {
        $sz = (Get-ChildItem -LiteralPath $d.FullName -Force -Recurse -ErrorAction SilentlyContinue | Measure-Object -Sum Length).Sum
        if($sz -gt 1GB){
          [pscustomobject]@{ Name=$d.Name; Path=$d.FullName; SizeGB=[math]::Round(($sz/1GB),2) }
        }
      } catch {}
    }
  ) | Sort-Object SizeGB -Descending | Select-Object -First 10
}

# Shadow storage (text, since size requires vssadmin)
try { $report.ShadowStorage = (vssadmin list shadowstorage) } catch {}

$outPath = Join-Path $PSScriptRoot '_disk_report.json'
$report | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $outPath
Write-Host "Wrote report to: $outPath"