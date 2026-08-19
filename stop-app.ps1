<#
    Stops everything start-app.ps1 launched.

    PostgreSQL is left running: it is a Windows service shared with anything
    else on this machine, and it starts with the box anyway.
#>
$stopped = @()

# tunnel
Get-Process cloudflared -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.Id -Force; $stopped += 'tunnel'
}

# backend (only this app's jar, not any other java process)
Get-CimInstance Win32_Process -Filter "Name='java.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*drishti-backend*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $stopped += 'backend' }

# inference
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*uvicorn*main:app*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $stopped += 'inference' }

# dashboard
Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*vite*preview*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $stopped += 'dashboard' }

if ($stopped) {
    Write-Host "Stopped: $($stopped | Select-Object -Unique | Sort-Object)" -ForegroundColor Green
} else {
    Write-Host "Nothing was running." -ForegroundColor DarkGray
}
Write-Host "PostgreSQL left running (Windows service)." -ForegroundColor DarkGray
