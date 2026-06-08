Get-CimInstance Win32_Process -Filter "Name = 'ngrok.exe' OR Name = 'node.exe' OR Name = 'docker-compose.exe' OR Name = 'docker.exe'" | Select-Object ProcessId, Name, CommandLine | Format-List | Out-String
Write-Host "---LISTENING PORTS (clinic-cms relevant)---"
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 1420, 5173, 8000, 8001, 8002, 4040, 5432 } | Select-Object LocalAddress, LocalPort, OwningProcess | Format-Table -AutoSize | Out-String
