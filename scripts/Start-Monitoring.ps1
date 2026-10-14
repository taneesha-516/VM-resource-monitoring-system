param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$serverPath = Join-Path $projectRoot 'server.py'
$runtimePath = Join-Path $projectRoot 'runtime'
$dashboardUrl = 'http://127.0.0.1:5000'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create .venv and install requirements.txt before starting monitoring.'
}
function Test-MonitorServer {
    try {
        $health = Invoke-RestMethod "$dashboardUrl/api/health" -TimeoutSec 2
        return $health.service -eq 'vm-resource-monitor' -and $health.status -eq 'ok'
    } catch { return $false }
}
if (-not (Test-MonitorServer)) {
    if (Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue) {
        throw 'Port 5000 belongs to another server. Stop that server before starting this project.'
    }
    New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
    $env:SERVER_HOST = '127.0.0.1'
    $env:SERVER_PORT = '5000'
    $env:DATABASE = Join-Path $projectRoot 'database\ubuntu-vm.db'
    $env:METRIC_INTERVAL = '5'
    $env:OFFLINE_TIMEOUT = '30'
    $serverProcess = Start-Process -FilePath $pythonPath -ArgumentList ('"' + $serverPath + '"') `
        -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $runtimePath 'server-output.log') `
        -RedirectStandardError (Join-Path $runtimePath 'server-error.log')
    Set-Content -LiteralPath (Join-Path $runtimePath 'server.pid') -Value $serverProcess.Id
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if (Test-MonitorServer) { $ready = $true; break }
        $serverProcess.Refresh()
        if ($serverProcess.HasExited) { break }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { throw "Server did not start. Read $runtimePath\server-error.log" }
}
Write-Output "Monitoring dashboard: $dashboardUrl"
if (-not $NoBrowser) { Start-Process $dashboardUrl }
