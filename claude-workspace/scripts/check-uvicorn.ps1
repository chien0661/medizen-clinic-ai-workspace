$proc = Get-CimInstance Win32_Process -Filter "ProcessId = 28816"
if ($proc) {
  Write-Host "CommandLine: $($proc.CommandLine)"
  Write-Host "WorkingSet: $($proc.WorkingSetSize)"
} else {
  Write-Host "PID 28816 not found"
}
Write-Host "---"
Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'uvicorn.exe'" | Where-Object { $_.CommandLine -match 'uvicorn|fastapi|clinic' } | Select-Object ProcessId, CommandLine | Format-List
