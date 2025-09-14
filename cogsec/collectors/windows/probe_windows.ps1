<# 
.SYNOPSIS
  Native endpoint probe for Windows: health + control posture + config checks.
  Emits JSON to stdout (or -JsonPath) and optionally appends a CSV line (-CsvPath).

.EXAMPLE
  # Run with ephemeral ExecPolicy bypass (safe default)
  powershell -NoProfile -ExecutionPolicy Bypass -File .\Get-CogSecEndpointState.ps1 \
    -CsvPath "C:\cogsec\health_metrics.csv" -JsonPath "-" -RequiredKBs KB5030211,KB5030213
#>

[CmdletBinding()]
param(
  [string]$CsvPath,
  [string]$JsonPath = "-",
  [string[]]$RequiredKBs = @(),
  [switch]$Quick
)

$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'

function Get-CpuPercent {
  try {
    $p = Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor | Where-Object Name -eq '_Total'
    return [double]$p.PercentProcessorTime
  } catch { return 0.0 }
}

function Get-MemPercent {
  try {
    $os = Get-CimInstance Win32_OperatingSystem
    $used = ($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)
    return [math]::Round(($used / [double]$os.TotalVisibleMemorySize) * 100, 2)
  } catch { return 0.0 }
}

function Get-DiskMaxPercent {
  try {
    $max = 0.0
    Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
      if ($_.Size -gt 0) {
        $pct = [math]::Round((($_.Size - $_.FreeSpace) / $_.Size) * 100, 2)
        if ($pct -gt $max) { $max = $pct }
      }
    }
    return $max
  } catch { return 0.0 }
}

function Get-FirewallEnabled {
  try {
    $p = Get-NetFirewallProfile
    return (@($p | Where-Object Enabled).Count -ge 1)
  } catch { return $null }
}

function Get-RdpEnabled {
  try {
    $v = (Get-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server').fDenyTSConnections
    return ($v -eq 0)
  } catch { return $null }
}

function Get-Controls {
  $avVendor = $null; $avEnabled=$null; $rtp=$null; $tamper=$null; $defsAge=$null
  if (Get-Command Get-MpComputerStatus -ErrorAction SilentlyContinue) {
    try {
      $mp = Get-MpComputerStatus
      $avVendor = "Windows Defender"
      $avEnabled = $mp.AntivirusEnabled
      $rtp = $mp.RealTimeProtectionEnabled
      $tamper = $mp.IsTamperProtected
      $defsAge = $mp.AntivirusSignatureAge
    } catch {}
  } else {
    try {
      $av = Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object -First 1
      if ($av) { $avVendor = $av.displayName }
    } catch {}
  }
  $avServices = @('WinDefend','Sense','SepMasterService','McShield','mfemms','xagt','csagent','CylanceSvc','ds_agent','Sophos Endpoint Defense Service')
  $svcStates = @{}
  foreach($n in $avServices){
    try { $s = Get-Service -Name $n -ErrorAction SilentlyContinue; if($s){ $svcStates[$n] = $s.Status.ToString() } } catch {}
  }
  return @{
    av_vendor = $avVendor
    av_enabled = $avEnabled
    rtp_enabled = $rtp
    tamper_protection = $tamper
    defs_age_days = $defsAge
    services = $svcStates
  }
}

function Get-Patch {
  if ($Quick) { return @{ patch_compliance_pct = $null; missing = @() } }
  $missing = @()
  try {
    $installed = Get-HotFix | ForEach-Object {$_.HotFixID}
    foreach($kb in $RequiredKBs){ if($kb -and -not ($installed -contains $kb)){ $missing += $kb } }
    if ($RequiredKBs.Count -gt 0) {
      $pct = [math]::Round((($RequiredKBs.Count - $missing.Count) / [double]$RequiredKBs.Count) * 100, 1)
      return @{ patch_compliance_pct = $pct; missing = $missing }
    }
  } catch {}
  return @{ patch_compliance_pct = $null; missing = $missing }
}

$now = (Get-Date).ToUniversalTime().ToString("o")
$hostName = $env:COMPUTERNAME
$os = (Get-CimInstance Win32_OperatingSystem).Caption

$rec = [ordered]@{
  host = $hostName
  timestamp = $now
  os = $os
  cpu = (Get-CpuPercent)
  mem = (Get-MemPercent)
  disk = (Get-DiskMaxPercent)
  net_in = 0
  net_out = 0
  firewall_enabled = (Get-FirewallEnabled)
  rdp_enabled = (Get-RdpEnabled)
  controls = (Get-Controls)
  patch = (Get-Patch)
}

# Emit JSON
$json = $rec | ConvertTo-Json -Depth 6
if ($JsonPath -and $JsonPath -ne '-') {
  $json | Out-File -FilePath $JsonPath -Encoding utf8
} else {
  Write-Output $json
}

# Append health CSV (for the workflow’s --health file)
if ($CsvPath) {
  if (-not (Test-Path $CsvPath)) {
    'host,timestamp,cpu,mem,disk,net_in,net_out' | Out-File -FilePath $CsvPath -Encoding utf8
  }
  ('{0},{1},{2},{3},{4},{5},{6}' -f $rec.host,$rec.timestamp,$rec.cpu,$rec.mem,$rec.disk,$rec.net_in,$rec.net_out) |
    Out-File -FilePath $CsvPath -Append -Encoding utf8
}
