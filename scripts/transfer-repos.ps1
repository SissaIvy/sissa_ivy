# Transfer selected repositories from SissaIvy -> mrobot787
# Prerequisites:
# - Create a Personal Access Token (classic) for SissaIvy with 'repo' scope
# - Paste it below

# Read PAT from environment variable or prompt the user securely
$SOURCE_PAT = $env:SISSAIVY_PAT
if (-not $SOURCE_PAT) {
    Write-Host "Enter the SissaIvy Personal Access Token (input will be hidden):"
    $securePat = Read-Host -AsSecureString
    $SOURCE_PAT = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePat)
    )
}
$TargetOwner = "mrobot787"

$Repos = @(
  "SissaIvy/Episodic-Memory-System-Python-",
  "SissaIvy/nlp-landing"
)

$Headers = @{
  "Authorization"          = "Bearer $SOURCE_PAT"
  "User-Agent"             = "gh-migrate"
  "Accept"                 = "application/vnd.github+json"
  "X-GitHub-Api-Version"   = "2022-11-28"
}

foreach ($repo in $Repos) {
  $repoName = $repo.Split('/')[1]
  $targetUri = "https://api.github.com/repos/$TargetOwner/$repoName"

  # Detect name conflict on target
  $exists = $false
  try {
    Invoke-RestMethod -Method Get -Uri $targetUri -ErrorAction Stop | Out-Null
    $exists = $true
  } catch { }

  $body = @{ new_owner = $TargetOwner }
  if ($exists) {
    $newName = "$repoName-from-SissaIvy"
    $body.new_name = $newName
    Write-Host "[$repo] Name conflict on target. Will transfer as '$newName'."
  }

  $transferUri = "https://api.github.com/repos/$repo/transfer"
  Write-Host "Transferring $repo → $TargetOwner ..."
  try {
    $null = Invoke-RestMethod -Headers $Headers -Method Post -Uri $transferUri `
      -ContentType "application/json" -Body ($body | ConvertTo-Json -Depth 5)
    Write-Host "Transfer request sent."
  } catch {
    Write-Host "Transfer request failed: $($_.Exception.Message)"
    continue
  }

  # Poll for new location (authenticated GET required for private repos)
  $finalName = if ($body.ContainsKey('new_name')) { $body.new_name } else { $repoName }
  $tries = 0
  do {
    Start-Sleep -Seconds 3
    $tries++
    try {
      Invoke-RestMethod -Headers $Headers -Method Get -Uri "https://api.github.com/repos/$TargetOwner/$finalName" -ErrorAction Stop | Out-Null
      Write-Host "Confirmed: https://github.com/$TargetOwner/$finalName"
      break
    } catch { }
  } while ($tries -lt 20)

  if ($tries -ge 20) {
    Write-Host "Still not visible; check your GitHub email(s) to accept/confirm the transfer if prompted."
  }
}

Write-Host "Done. Watch for GitHub emails to accept/confirm transfers if required."