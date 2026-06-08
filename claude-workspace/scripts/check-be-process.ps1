Get-Process | Where-Object { $_.Name -match 'docker|uvicorn|python' } | Select-Object Name, Id, MainWindowTitle | Format-Table -AutoSize
