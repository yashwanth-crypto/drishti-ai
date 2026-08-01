<#
    Starts Drishti-AI and opens a public URL.

    Usage:   .\start-app.ps1            # local + public tunnel
             .\start-app.ps1 -NoTunnel  # local only, no public URL

    PostgreSQL runs as a Windows service and starts with the machine, so it is
    only checked here, not started.
#>
param([switch]$NoTunnel)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$logs = Join-Path $root '.run'
New-Item -ItemType Directory -Force -Path $logs | Out-Null

$java  = 'C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot\bin\java.exe'
$cfd   = 'C:\Program Files (x86)\cloudflared\cloudflared.exe'
$py    = Join-Path $root '.venv\Scripts\python.exe'

function Wait-Url($url, $name, $seconds = 90) {
    for ($i = 0; $i -lt $seconds; $i++) {
        try {
            Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 2 | Out-Null
            Write-Host "  $name ready" -ForegroundColor Green
            return $true
        } catch {
            # A 401 means it answered, which is all we are checking for.
            if ($_.Exception.Response.StatusCode.value__) {
                Write-Host "  $name ready" -ForegroundColor Green
                return $true
            }
        }
        Start-Sleep -Seconds 1
    }
    Write-Host "  $name did NOT come up - see $logs" -ForegroundColor Red
    return $false
}

# ---- 1. database -----------------------------------------------------------
Write-Host "`nDrishti-AI" -ForegroundColor Cyan
$pg = Get-Service postgresql-x64-16 -ErrorAction SilentlyContinue
if (-not $pg) { throw "PostgreSQL service not found. Reinstall PostgreSQL 16." }
if ($pg.Status -ne 'Running') { Start-Service postgresql-x64-16; Start-Sleep 3 }
Write-Host "  database ready" -ForegroundColor Green

# ---- 2. credentials --------------------------------------------------------
# Without a real JWT_SECRET the app falls back to the development key that is
# committed to the repo, so tokens anyone could forge would be accepted.
$secretsPath = Join-Path $root 'app\secrets.local.json'
if (-not (Test-Path $secretsPath)) {
    throw "Missing $secretsPath - the JWT secret and account passwords live there."
}
$secrets = Get-Content $secretsPath -Raw | ConvertFrom-Json

# ---- 3. inference ----------------------------------------------------------
Start-Process -FilePath $py `
    -ArgumentList '-m','uvicorn','main:app','--port','8000','--host','127.0.0.1' `
    -WorkingDirectory (Join-Path $root 'app\inference') `
    -WindowStyle Minimized
Wait-Url 'http://127.0.0.1:8000/health' 'inference' | Out-Null

# ---- 4. backend ------------------------------------------------------------
Start-Process -FilePath 'powershell' `
    -ArgumentList '-NoProfile','-Command',
        "`$env:JWT_SECRET='$($secrets.jwt_secret)'; `$env:SEED_USERS='false'; & '$java' -jar target\drishti-backend-1.0.0.jar" `
    -WorkingDirectory (Join-Path $root 'app\backend') `
    -WindowStyle Minimized
Wait-Url 'http://localhost:8080/actuator/health' 'backend' | Out-Null

# ---- 5. dashboard ----------------------------------------------------------
# Serves the built bundle, not the dev server: no HMR socket, no source maps.
# Calls the local vite.cmd directly -- going through `cmd /c npx` adds two
# process layers, and the server dies with them rather than outliving the script.
$vite = Join-Path $root 'dashboard\node_modules\.bin\vite.cmd'
if (-not (Test-Path $vite)) { throw "vite not found - run 'npm install' in dashboard\" }
if (-not (Test-Path (Join-Path $root 'dashboard\dist\index.html'))) {
    Write-Host "  building dashboard..." -ForegroundColor DarkGray
    & (Join-Path $root 'dashboard\node_modules\.bin\vite.cmd') build --config (Join-Path $root 'dashboard\vite.config.js') | Out-Null
}
Start-Process -FilePath $vite `
    -ArgumentList 'preview','--port','4173' `
    -WorkingDirectory (Join-Path $root 'dashboard') `
    -WindowStyle Minimized
Wait-Url 'http://localhost:4173' 'dashboard' | Out-Null

Write-Host "`n  Local:  http://localhost:4173" -ForegroundColor White

# ---- 6. public tunnel ------------------------------------------------------
if (-not $NoTunnel) {
    if (-not (Test-Path $cfd)) {
        Write-Host "  cloudflared not installed - skipping public URL" -ForegroundColor Yellow
    } else {
        $tunnelLog = Join-Path $logs 'tunnel.log'
        Remove-Item $tunnelLog -ErrorAction SilentlyContinue
        # --logfile rather than -RedirectStandardError: redirecting hands the
        # child a pipe owned by this script, and cloudflared dies with it when
        # the script's console goes away.
        Start-Process -FilePath $cfd `
            -ArgumentList 'tunnel','--url','http://localhost:4173','--no-autoupdate',
                          '--logfile',$tunnelLog,'--loglevel','info' `
            -WindowStyle Minimized

        Write-Host "  opening public URL..." -NoNewline
        $public = $null
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Seconds 1
            if (Test-Path $tunnelLog) {
                $m = Select-String -Path $tunnelLog -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' |
                     Select-Object -First 1
                if ($m) { $public = $m.Matches[0].Value; break }
            }
        }
        Write-Host ""
        if ($public) {
            Write-Host "  Public: $public" -ForegroundColor Yellow
            Set-Clipboard -Value $public
            Write-Host "          (copied to clipboard - changes every restart)" -ForegroundColor DarkGray
        } else {
            Write-Host "  tunnel did not report a URL - see $tunnelLog" -ForegroundColor Red
        }
    }
}

# ---- 7. sign-in ------------------------------------------------------------
Write-Host "`n  Sign in" -ForegroundColor Cyan
Write-Host "    owner     $($secrets.owner_user) / $($secrets.owner_pass)"
Write-Host "    operator  $($secrets.operator_user) / $($secrets.operator_pass)"
Write-Host "`n  Stop everything with .\stop-app.ps1`n" -ForegroundColor DarkGray
