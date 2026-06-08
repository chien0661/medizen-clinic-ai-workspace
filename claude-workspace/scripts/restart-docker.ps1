Write-Host "=== Step 1: Kill zombie docker compose processes ==="
$zombies = Get-Process -Id 17152, 26088 -ErrorAction SilentlyContinue
foreach ($p in $zombies) {
  Write-Host "Killing PID $($p.Id) ($($p.Name))"
  Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "=== Step 2: Try start com.docker.service (may need admin) ==="
try {
  Start-Service com.docker.service -ErrorAction Stop
  Write-Host "Service started OK"
} catch {
  Write-Host ("Start-Service failed: " + $_.Exception.Message)
  Write-Host "Falling back to GUI launch..."
  $dockerExe = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
  if (Test-Path $dockerExe) {
    Start-Process $dockerExe
    Write-Host ("Launched: " + $dockerExe)
  } else {
    Write-Host ("Docker Desktop.exe NOT FOUND at " + $dockerExe)
  }
}

Write-Host ""
Write-Host "=== Step 3: Wait for daemon (up to 90s) ==="
$pipePath = "\\.\pipe\dockerDesktopLinuxEngine"
$ok = $false
for ($i = 1; $i -le 18; $i++) {
  Start-Sleep -Seconds 5
  $exists = Test-Path -LiteralPath $pipePath
  if ($exists) {
    Write-Host ("[" + ($i*5) + "s] Pipe exists - testing daemon...")
    $r = & docker info 2>&1 | Out-String
    if ($r -notmatch "error during connect|Cannot connect") {
      Write-Host ("Docker daemon UP after " + ($i*5) + "s")
      $ok = $true
      break
    }
  } else {
    Write-Host ("[" + ($i*5) + "s] Pipe not yet...")
  }
}
if (-not $ok) {
  Write-Host "FAILED: Docker daemon still not responding after 90s"
}
