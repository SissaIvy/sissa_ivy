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
  [switch]$Quick,
  [Alias('SkipPatch')][switch]$QuickPatch,
  [int]$SampleSeconds = 0,
  [switch]$Diagnostics,
  [string[]]$AdditionalServices = @()
)

$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'

function Get-CpuPercent {
  try {
    $p = Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor | Where-Object Name -eq '_Total'
    return [double]$p.PercentProcessorTime
  } catch {
    Add-DiagError 'cpu' $_
    return 0.0
  }
}

function Get-MemPercent {
  try {
    $os = Get-CimInstance Win32_OperatingSystem
    $used = ($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)
    return [math]::Round(($used / [double]$os.TotalVisibleMemorySize) * 100, 2)
  } catch {
    Add-DiagError 'memory' $_
    return 0.0
  }
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
  } catch {
    Add-DiagError 'disk' $_
    return 0.0
  }
}

function Get-FirewallEnabled {
  try {
    $p = Get-NetFirewallProfile
    return (@($p | Where-Object Enabled).Count -ge 1)
  } catch {
    Add-DiagError 'firewall' $_
    return $null
  }
}

function Get-RdpEnabled {
  try {
    $v = (Get-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server').fDenyTSConnections
    return ($v -eq 0)
  } catch {
    Add-DiagError 'rdp' $_
    return $null
  }
}

function Get-RdpNLAEnabled {
  try {
    $path = 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp'
    $sec = (Get-ItemProperty -Path $path -ErrorAction Stop)
    # UserAuthentication = 1 indicates NLA required
    return ($sec.UserAuthentication -eq 1)
  } catch {
    Add-DiagError 'rdp_nla' $_
    return $null
  }
}

function Add-DiagError($component, $err){
  if ($Diagnostics){
    $script:DiagErrors += [pscustomobject]@{
      component = $component
      message   = ($err.Exception.Message | Out-String).Trim()
    }
  }
}

$script:DiagErrors = @()

function Get-FailedLoginAttempts {
  $attempts = @{ count_24h = 0; unique_users = @(); sources = @() }
  try {
    # Check Windows Event Log for failed logon events (Event ID 4625)
    $yesterday = (Get-Date).AddDays(-1)
    $events = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625; StartTime=$yesterday} -MaxEvents 100 -ErrorAction SilentlyContinue
    
    if ($events) {
      $attempts.count_24h = $events.Count
      $users = $events | ForEach-Object {
        $xml = [xml]$_.ToXml()
        $userData = $xml.Event.EventData.Data | Where-Object Name -eq 'TargetUserName'
        if ($userData) { $userData.'#text' }
      } | Where-Object { $_ -and $_ -ne '-' } | Sort-Object -Unique
      $attempts.unique_users = $users
      $attempts.sources += 'Security'
    }
    
    # Check for failed RDP attempts (Event ID 4625 with LogonType 10)
    $rdpEvents = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625; StartTime=$yesterday} -MaxEvents 50 -ErrorAction SilentlyContinue |
      Where-Object { $_.Message -match 'Logon Type:\s*10' }
    if ($rdpEvents) {
      $attempts.rdp_failures = $rdpEvents.Count
      $attempts.sources += 'RDP'
    }
  } catch {
    Add-DiagError 'failed_logins' $_
  }
  return $attempts
}

function Get-UsbDeviceMonitoring {
  $usbInfo = @{ connected_devices = @(); recent_events = 0; policy_compliant = $true }
  try {
    # Get currently connected USB devices
    $usbDevices = Get-CimInstance -ClassName Win32_USBControllerDevice -ErrorAction SilentlyContinue |
      ForEach-Object { Get-CimInstance -InputObject $_.Dependent -ErrorAction SilentlyContinue } |
      Where-Object { $_.DeviceID -match '^USB' }
    
    foreach ($device in $usbDevices) {
      $usbInfo.connected_devices += @{
        device_id = $device.DeviceID
        description = $device.Description
        manufacturer = $device.Manufacturer
        status = $device.Status
      }
    }
    
    # Check for recent USB device events in System log
    $yesterday = (Get-Date).AddDays(-1)
    $usbEvents = Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$yesterday} -MaxEvents 100 -ErrorAction SilentlyContinue |
      Where-Object { $_.Message -match 'USB|removable' }
    $usbInfo.recent_events = if ($usbEvents) { $usbEvents.Count } else { 0 }
    
    # Check USB storage policy compliance
    try {
      $usbPolicy = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\USBSTOR' -Name Start -ErrorAction SilentlyContinue
      if ($usbPolicy -and $usbPolicy.Start -eq 4) {
        $usbInfo.storage_disabled = $true
      }
    } catch { }
    
  } catch {
    Add-DiagError 'usb_monitoring' $_
  }
  return $usbInfo
}

function Get-FileIntegrityMonitoring {
  $integrity = @{ files_checked = 0; modified_files = @(); missing_files = @(); critical_changes = @() }
  
  # Critical Windows system files to monitor
  $criticalFiles = @(
    'C:\Windows\System32\drivers\etc\hosts',
    'C:\Windows\System32\config\SAM',
    'C:\Windows\System32\config\SYSTEM',
    'C:\Windows\System32\config\SECURITY',
    'C:\Windows\System32\GroupPolicy\Machine\Registry.pol',
    'C:\Windows\System32\GroupPolicy\User\Registry.pol'
  )
  
  try {
    foreach ($file in $criticalFiles) {
      $integrity.files_checked++
      
      if (-not (Test-Path $file)) {
        $integrity.missing_files += $file
        continue
      }
      
      try {
        $fileInfo = Get-ItemProperty $file -ErrorAction Stop
        $lastWrite = $fileInfo.LastWriteTime
        
        # Check if file was modified in last 24 hours
        if ($lastWrite -gt (Get-Date).AddDays(-1)) {
          $integrity.modified_files += @{
            path = $file
            last_modified = $lastWrite.ToString('o')
            size = $fileInfo.Length
          }
        }
        
        # Check for suspicious locations/names
        if ($file -match '(hosts|sam|system|security)' -and $lastWrite -gt (Get-Date).AddHours(-1)) {
          $integrity.critical_changes += @{
            path = $file
            change_time = $lastWrite.ToString('o')
            risk_level = 'high'
          }
        }
      } catch {
        Add-DiagError "file_integrity_$file" $_
      }
    }
  } catch {
    Add-DiagError 'file_integrity' $_
  }
  return $integrity
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
  $avServices = @('WinDefend','Sense','SepMasterService','McShield','mfemms','xagt','csagent','CylanceSvc','ds_agent','Sophos Endpoint Defense Service') + $AdditionalServices
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
  if ($Quick -or $QuickPatch) { return @{ patch_compliance_pct = $null; missing = @(); required_total = $RequiredKBs.Count; missing_count = $null } }
  $missing = @()
  try {
    $installed = Get-HotFix | ForEach-Object {$_.HotFixID}
    foreach($kb in $RequiredKBs){ if($kb -and -not ($installed -contains $kb)){ $missing += $kb } }
    $total = $RequiredKBs.Count
    if ($total -gt 0) {
      $pct = [math]::Round((($total - $missing.Count) / [double]$total) * 100, 1)
      return @{ patch_compliance_pct = $pct; missing = $missing; required_total = $total; missing_count = $missing.Count }
    }
  } catch {
    Add-DiagError 'patch' $_
  }
  return @{ patch_compliance_pct = $null; missing = $missing; required_total = $RequiredKBs.Count; missing_count = $missing.Count }
}

function Sample-NetworkIO {
  param([int]$Seconds = 0)
  $baseline = @{}
  $filterIf = { param($n) -not ($n -match 'Loopback|isatap|Teredo') }
  try {
    Get-CimInstance Win32_PerfFormattedData_Tcpip_NetworkInterface | ForEach-Object {
      if (& $filterIf $_.Name) { $baseline[$_.Name] = [pscustomobject]@{ in=$_.BytesReceivedPerSec; out=$_.BytesSentPerSec } }
    }
  } catch { Add-DiagError 'net_baseline' $_ }
  if ($Seconds -le 0){ return @{ in_bps = 0; out_bps = 0 } }
  Start-Sleep -Seconds $Seconds
  $after = @{}
  try {
    Get-CimInstance Win32_PerfFormattedData_Tcpip_NetworkInterface | ForEach-Object {
      if (& $filterIf $_.Name) { $after[$_.Name] = [pscustomobject]@{ in=$_.BytesReceivedPerSec; out=$_.BytesSentPerSec } }
    }
  } catch { Add-DiagError 'net_after' $_ }
  $in = 0; $out = 0
  foreach($k in $baseline.Keys){
    if ($after.ContainsKey($k)) {
      $in += ($baseline[$k].in + $after[$k].in) / 2
      $out += ($baseline[$k].out + $after[$k].out) / 2
    }
  }
  return @{ in_bps = [math]::Round($in,0); out_bps = [math]::Round($out,0) }
}

function Smooth-Sample {
  param([int]$Seconds,[scriptblock]$Producer)
  if ($Seconds -le 0){ return & $Producer }
  $acc = 0.0; $n = 0
  $interval = [math]::Max([int][math]::Ceiling($Seconds/2),1)
  $deadline = (Get-Date).AddSeconds($Seconds)
  while((Get-Date) -lt $deadline){
    try { $v = & $Producer; if ($v -is [double] -or $v -is [int]) { $acc += [double]$v; $n++ } } catch { }
    Start-Sleep -Milliseconds ($interval*500)
  }
  if ($n -gt 0){ return [math]::Round($acc / $n,2) } else { return & $Producer }
}

$now = (Get-Date).ToUniversalTime().ToString("o")
$hostName = $env:COMPUTERNAME
$os = (Get-CimInstance Win32_OperatingSystem).Caption

if ($SampleSeconds -gt 0){
  $cpuVal = Smooth-Sample -Seconds $SampleSeconds -Producer { Get-CpuPercent }
  $memVal = Smooth-Sample -Seconds $SampleSeconds -Producer { Get-MemPercent }
  $diskVal = Get-DiskMaxPercent
  $netVals = Sample-NetworkIO -Seconds $SampleSeconds
} else {
  $cpuVal = Get-CpuPercent
  $memVal = Get-MemPercent
  $diskVal = Get-DiskMaxPercent
  $netVals = @{ in_bps = 0; out_bps = 0 }
}

$rec = [ordered]@{
  schema_version = '1.2.0'
  host = $hostName
  timestamp = $now
  os = $os
  cpu = $cpuVal
  mem = $memVal
  disk = $diskVal
  net_in_bps = $netVals.in_bps
  net_out_bps = $netVals.out_bps
  firewall_enabled = (Get-FirewallEnabled)
  rdp_enabled = (Get-RdpEnabled)
  rdp_nla_enabled = (Get-RdpNLAEnabled)
  controls = (Get-Controls)
  patch = (Get-Patch)
  security = @{
    failed_logins = (Get-FailedLoginAttempts)
    usb_devices = (Get-UsbDeviceMonitoring)
    file_integrity = (Get-FileIntegrityMonitoring)
  }
}

# Backward compatibility alias fields (deprecated); maintained for consumers expecting legacy names.
$rec.net_in = $rec.net_in_bps
$rec.net_out = $rec.net_out_bps

if ($Diagnostics -and $script:DiagErrors.Count -gt 0){
  $rec.errors = $script:DiagErrors
}

# Emit JSON
$json = $rec | ConvertTo-Json -Depth 6
if ($JsonPath -and $JsonPath -ne '-') {
  $json | Out-File -FilePath $JsonPath -Encoding utf8
} else {
  Write-Output $json
}

# Append health CSV (extended metrics)
if ($CsvPath) {
  $csvObj = [pscustomobject]@{
    host        = $rec.host
    timestamp   = $rec.timestamp
    cpu         = $rec.cpu
    mem         = $rec.mem
    disk        = $rec.disk
    net_in_bps  = $rec.net_in_bps
    net_out_bps = $rec.net_out_bps
  }
  if (-not (Test-Path $CsvPath)) {
    $csvObj | Export-Csv -Path $CsvPath -NoTypeInformation -Encoding UTF8
  } else {
    $csvObj | Export-Csv -Path $CsvPath -NoTypeInformation -Append -Encoding UTF8
  }
}
