param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoInstall,
    [string]$HostAddress = "127.0.0.1",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$RunDir = Join-Path $RootDir ".run"
$BackendPidFile = Join-Path $RunDir "backend.pid"
$FrontendPidFile = Join-Path $RunDir "frontend.pid"
$BackendLog = Join-Path $RunDir "backend.log"
$BackendErrLog = Join-Path $RunDir "backend.err.log"
$FrontendLog = Join-Path $RunDir "frontend.log"
$FrontendErrLog = Join-Path $RunDir "frontend.err.log"

if ($BackendOnly -and $FrontendOnly) {
    throw "Use only one of -BackendOnly or -FrontendOnly."
}

if (-not (Test-Path -LiteralPath $RunDir)) {
    New-Item -ItemType Directory -Path $RunDir | Out-Null
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host $Message
}

function Require-Command {
    param(
        [string]$Name,
        [string]$InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' was not found. $InstallHint"
    }
}

function Test-ProcessAlive {
    param([string]$PidFile)

    if (-not (Test-Path -LiteralPath $PidFile)) {
        return $false
    }

    $rawPid = (Get-Content -LiteralPath $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    $processId = 0
    if (-not [int]::TryParse($rawPid, [ref]$processId)) {
        Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
        return $false
    }

    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
        return $false
    }

    return $true
}

function Assert-PortFree {
    param(
        [int]$Port,
        [string]$ServiceName
    )

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        return
    }

    $ownerPid = ($connections | Select-Object -First 1).OwningProcess
    $owner = Get-Process -Id $ownerPid -ErrorAction SilentlyContinue
    $ownerName = if ($owner) { $owner.ProcessName } else { "unknown" }
    throw "$ServiceName port $Port is already in use by PID $ownerPid ($ownerName). Run .\scripts\windows\stop.ps1 first or choose another port."
}

function Wait-Port {
    param(
        [string]$Name,
        [string]$ConnectHost,
        [int]$Port,
        [int]$TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $client = [System.Net.Sockets.TcpClient]::new()
            $task = $client.ConnectAsync($ConnectHost, $Port)
            if ($task.Wait(1000) -and $client.Connected) {
                $client.Dispose()
                Write-Host "  $Name is listening on http://localhost:$Port"
                return
            }
            $client.Dispose()
        } catch {
            Start-Sleep -Milliseconds 500
        }
        Start-Sleep -Milliseconds 500
    }

    throw "$Name did not start within $TimeoutSeconds seconds. Check logs in $RunDir."
}

function Ensure-BackendEnv {
    $envPath = Join-Path $BackendDir ".env"
    $envExamplePath = Join-Path $BackendDir ".env.example"

    if ((-not (Test-Path -LiteralPath $envPath)) -and (Test-Path -LiteralPath $envExamplePath)) {
        Copy-Item -LiteralPath $envExamplePath -Destination $envPath
        Write-Host "  Created backend\.env from backend\.env.example. Set DEEPSEEK_API_KEY before using AI features."
    }
}

function Start-Backend {
    if (Test-ProcessAlive $BackendPidFile) {
        $existingPid = Get-Content -LiteralPath $BackendPidFile | Select-Object -First 1
        Write-Host "Backend already appears to be running (PID $existingPid)."
        return
    }

    Assert-PortFree -Port $BackendPort -ServiceName "Backend"
    Require-Command -Name "uv" -InstallHint "Install uv first: https://docs.astral.sh/uv/"

    $venvDir = Join-Path $BackendDir ".venv"
    $pythonExe = Join-Path $venvDir "Scripts\python.exe"

    Write-Step "[1/4] Preparing backend virtual environment"
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        Push-Location $BackendDir
        try {
            & uv venv
        } finally {
            Pop-Location
        }
    }

    if (-not (Test-Path -LiteralPath $pythonExe)) {
        throw "Backend virtual environment was not created at $venvDir."
    }

    Ensure-BackendEnv

    if (-not $NoInstall) {
        Write-Step "[2/4] Installing backend dependencies"
        Push-Location $BackendDir
        try {
            & uv pip install --python $pythonExe -r requirements.txt
        } finally {
            Pop-Location
        }
    } else {
        Write-Step "[2/4] Skipping backend dependency install (-NoInstall)"
    }

    Write-Step "[3/4] Starting backend on port $BackendPort"
    $backendArgs = @(
        "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--host", $HostAddress,
        "--port", "$BackendPort"
    )
    $process = Start-Process `
        -FilePath $pythonExe `
        -ArgumentList $backendArgs `
        -WorkingDirectory $BackendDir `
        -RedirectStandardOutput $BackendLog `
        -RedirectStandardError $BackendErrLog `
        -WindowStyle Hidden `
        -PassThru

    Set-Content -LiteralPath $BackendPidFile -Value $process.Id
    $connectHost = if ($HostAddress -eq "0.0.0.0") { "127.0.0.1" } else { $HostAddress }
    Wait-Port -Name "Backend" -ConnectHost $connectHost -Port $BackendPort
}

function Start-Frontend {
    if (Test-ProcessAlive $FrontendPidFile) {
        $existingPid = Get-Content -LiteralPath $FrontendPidFile | Select-Object -First 1
        Write-Host "Frontend already appears to be running (PID $existingPid)."
        return
    }

    Assert-PortFree -Port $FrontendPort -ServiceName "Frontend"
    Require-Command -Name "npm" -InstallHint "Install Node.js/npm first."

    Write-Step "[4/4] Preparing frontend"
    if ((-not $NoInstall) -and (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules")))) {
        Push-Location $FrontendDir
        try {
            if (Test-Path -LiteralPath (Join-Path $FrontendDir "package-lock.json")) {
                & npm ci
            } else {
                & npm install
            }
        } finally {
            Pop-Location
        }
    } elseif ($NoInstall) {
        Write-Host "  Skipping frontend dependency install (-NoInstall)"
    } else {
        Write-Host "  node_modules already exists"
    }

    Write-Host "  Starting frontend on port $FrontendPort"
    $frontendArgs = @("run", "dev", "--", "--host", $HostAddress, "--port", "$FrontendPort")
    $process = Start-Process `
        -FilePath "npm.cmd" `
        -ArgumentList $frontendArgs `
        -WorkingDirectory $FrontendDir `
        -RedirectStandardOutput $FrontendLog `
        -RedirectStandardError $FrontendErrLog `
        -WindowStyle Hidden `
        -PassThru

    Set-Content -LiteralPath $FrontendPidFile -Value $process.Id
    $connectHost = if ($HostAddress -eq "0.0.0.0") { "127.0.0.1" } else { $HostAddress }
    Wait-Port -Name "Frontend" -ConnectHost $connectHost -Port $FrontendPort
}

Write-Host "================================================"
Write-Host " Starting HR Interview Analysis System"
Write-Host "================================================"

if (-not $FrontendOnly) {
    Start-Backend
}

if (-not $BackendOnly) {
    Start-Frontend
}

Write-Host ""
Write-Host "================================================"
if (-not $FrontendOnly) {
    Write-Host " Backend:  http://localhost:$BackendPort"
}
if (-not $BackendOnly) {
    Write-Host " Frontend: http://localhost:$FrontendPort"
}
Write-Host " Logs:     $RunDir"
Write-Host " Stop:     .\scripts\windows\stop.ps1"
Write-Host "================================================"
