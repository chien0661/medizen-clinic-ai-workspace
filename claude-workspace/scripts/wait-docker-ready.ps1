Write-Host "Waiting for Docker daemon to be FULLY ready (Linux engine + WSL)..."
$ok = $false
for ($i = 1; $i -le 36; $i++) {
  Start-Sleep -Seconds 5
  $r = & docker info 2>&1 | Out-String
  if ($r -match "Server Version" -and $r -notmatch "Internal Server Error") {
    Write-Host ("[" + ($i*5) + "s] Daemon FULLY ready")
    $ok = $true
    break
  } else {
    $shortErr = ($r -split "`n")[0..1] -join " | "
    Write-Host ("[" + ($i*5) + "s] still init: " + $shortErr.Substring(0, [Math]::Min(100, $shortErr.Length)))
  }
}
if (-not $ok) { Write-Host "FAILED after 180s" }
