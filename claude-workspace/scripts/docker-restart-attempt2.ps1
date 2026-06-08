Write-Host "=== Current Docker processes ==="
Get-Process | Where-Object { $_.Name -match 'Docker' } | Select-Object Name, Id | Format-Table -AutoSize | Out-String

Write-Host "=== Killing all Docker Desktop processes ==="
Get-Process | Where-Object { $_.Name -match 'Docker' } | ForEach-Object {
  Write-Host ("Killing " + $_.Name + " PID " + $_.Id)
  Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "=== Re-launching Docker Desktop ==="
$dockerExe = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerExe) {
  Start-Process $dockerExe
  Write-Host ("Launched: " + $dockerExe)
} else {
  Write-Host ("NOT FOUND: " + $dockerExe)
  exit 1
}

Write-Host ""
Write-Host "=== Wait for daemon FULL ready (test docker info Server line) ==="
$pipePath = "\\.\pipe\dockerDesktopLinuxEngine"
$ok = $false
for ($i = 1; $i -le 30; $i++) {
  Start-Sleep -Seconds 5
  $exists = Test-Path -LiteralPath $pipePath
  if ($exists) {
    $r = & docker info 2>&1 | Out-String
    if ($r -match "Server Version: \d") {
      Write-Host ("[" + ($i*5) + "s] Daemon FULLY ready (server version detected)")
      $ok = $true
      break
    } else {
      $serverLine = ($r -split "`r?`n") | Where-Object { $_ -match "Server|ERROR" } | Select-Object -First 2
      Write-Host ("[" + ($i*5) + "s] pipe ok, daemon not ready: " + ($serverLine -join " | "))
    }
  } else {
    Write-Host ("[" + ($i*5) + "s] pipe not yet")
  }
}
if (-not $ok) {
  Write-Host "FAILED after 150s"
  exit 1
}
Write-Host "OK"
