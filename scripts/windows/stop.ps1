param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$RunDir = Join-Path $RootDir ".run"
$BackendPidFile = Join-Path $RunDir "backend.pid"
$FrontendPidFile = Join-Path $RunDir "frontend.pid"

if ($BackendOnly -and $FrontendOnly) {
    throw "Use only one of -BackendOnly or -FrontendOnly."
}

function Get-ChildProcessIds {
    param([int]$ParentId)

    try {
        Get-CimInstance Win32_Process -Filter "ParentProcessId=$ParentId" |
            ForEach-Object { [int]$_.ProcessId }
    } catch {
        @()
    }
}

function Stop-ProcessTree {
    param([int]$ProcessId)

    foreach ($childId in Get-ChildProcessIds -ParentId $ProcessId) {
        Stop-ProcessTree -ProcessId $childId
    }

    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -ne $process) {
        Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    }
}

function Stop-ServiceFromPidFile {
    param(
        [string]$Name,
        [string]$PidFile,
        [int]$FallbackPort,
        [string[]]$CommandNeedles
    )

    Write-Host "Stopping $Name..."

    if (-not (Test-Path -LiteralPath $PidFile)) {
        Write-Host "  No pid file found."
        Stop-ServiceByPort -Name $Name -Port $FallbackPort -CommandNeedles $CommandNeedles
        return
    }

    $rawPid = Get-Content -LiteralPath $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    $processId = 0
    if ([int]::TryParse($rawPid, [ref]$processId)) {
        Stop-ProcessTree -ProcessId $processId
        Write-Host "  Stopped PID $processId."
    } else {
        Write-Host "  Ignored invalid pid file."
    }

    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
}

function Stop-ServiceByPort {
    param(
        [string]$Name,
        [int]$Port,
        [string[]]$CommandNeedles
    )

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        return
    }

    $ownerIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($ownerId in $ownerIds) {
        $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerId" -ErrorAction SilentlyContinue
        $commandLine = if ($cim -and $cim.CommandLine) { $cim.CommandLine.ToLowerInvariant() } else { "" }
        $matched = $false

        foreach ($needle in $CommandNeedles) {
            if ($commandLine.Contains($needle.ToLowerInvariant())) {
                $matched = $true
                break
            }
        }

        if ($matched) {
            Stop-ProcessTree -ProcessId ([int]$ownerId)
            Write-Host "  Stopped process on port $Port (PID $ownerId)."
        } else {
            Write-Host "  Port $Port is used by PID $ownerId, but it does not look like $Name. Skipped."
        }
    }
}

if (-not $FrontendOnly) {
    Stop-ServiceFromPidFile `
        -Name "backend" `
        -PidFile $BackendPidFile `
        -FallbackPort $BackendPort `
        -CommandNeedles @("uvicorn", "app.main:app")
}

if (-not $BackendOnly) {
    Stop-ServiceFromPidFile `
        -Name "frontend" `
        -PidFile $FrontendPidFile `
        -FallbackPort $FrontendPort `
        -CommandNeedles @("vite", "npm")
}

Write-Host "Done."
