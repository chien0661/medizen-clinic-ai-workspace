#requires -Version 5.1
<#
.SYNOPSIS
    Launch 5 parallel Claude Code dev agents -- each in its own PowerShell window.

.DESCRIPTION
    Spawns 5 separate `claude` sessions, each scoped to a distinct task track:
      BE-A (core)         : 001 -> 002 -> 003 -> 004 -> 005 -> 007 -> 009
      BE-B (inv/billing)  : 006 -> 012 -> 011 -> 013
      BE-C (operations)   : 008 -> 010 -> 014 -> 015
      FE-1 (clinical)     : 016 -> 017 -> 018 -> 019 -> 024
      FE-2 (support)      : 020 -> 021 -> 022 -> 023

    Each agent reads docs/tasks/dashboard.md, picks the next unblocked task in its
    track queue, and runs the full multi-agent workflow (Implementation -> Review
    -> Test -> Documentation) via the existing `manager` skill.

.PARAMETER Tracks
    Optional. Comma-separated list of track names to launch (default: all 5).
    Example: -Tracks "BE-A,FE-1"

.PARAMETER DryRun
    Show what would launch without opening any window.

.EXAMPLE
    .\scripts\launch-parallel-devs.ps1
    # Launches all 5 tracks

.EXAMPLE
    .\scripts\launch-parallel-devs.ps1 -Tracks "BE-A,BE-B"
    # Launches only the 2 BE tracks

.EXAMPLE
    .\scripts\launch-parallel-devs.ps1 -DryRun
    # Print the launch plan, do not open anything
#>

[CmdletBinding()]
param(
    [string]$Tracks = "BE-A,BE-B,BE-C,FE-1,FE-2",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$workspaceRoot = (Resolve-Path "$PSScriptRoot\..").Path

# ---------------------------------------------------------------------------
# Track definitions
# ---------------------------------------------------------------------------
$trackDefs = @{
    "BE-A" = @{
        Title = "BE-A | Core Pipeline"
        Queue = "TASK-001, TASK-002, TASK-003, TASK-004, TASK-005, TASK-007, TASK-009"
        Focus = "Foundation, Tenancy/RLS, Auth, RBAC, Patient, Visit, Vitals"
    }
    "BE-B" = @{
        Title = "BE-B | Inventory & Billing"
        Queue = "TASK-006, TASK-012, TASK-011, TASK-013"
        Focus = "Settings/Onboarding, Inventory FEFO, Prescription, Invoice/Payment"
    }
    "BE-C" = @{
        Title = "BE-C | Operations"
        Queue = "TASK-008, TASK-010, TASK-014, TASK-015"
        Focus = "Appointment/Queue, Service Catalog, HR, Reports/Notifications/Jobs"
    }
    "FE-1" = @{
        Title = "FE-1 | Clinical UI"
        Queue = "TASK-016, TASK-017, TASK-018, TASK-019, TASK-024"
        Focus = "Tauri Shell, Auth/Design System, Reception, Doctor, Dashboard"
    }
    "FE-2" = @{
        Title = "FE-2 | Support UI"
        Queue = "TASK-020, TASK-021, TASK-022, TASK-023"
        Focus = "Pharmacy, Billing, HR, Admin"
    }
}

$selected = $Tracks.Split(",") | ForEach-Object { $_.Trim() }

# ---------------------------------------------------------------------------
# Build the per-track prompt
# ---------------------------------------------------------------------------
function Build-Prompt {
    param([string]$TrackName, [hashtable]$Track)

    return @"
You are the **$TrackName dev agent** for the Clinic CMS project.

## Your scope
- Track: $($Track.Title)
- Focus: $($Track.Focus)
- Task queue (sequential within this track): $($Track.Queue)

## Operating rules
1. Read ``docs/tasks/dashboard.md`` to see current status of every task.
2. Pick the FIRST task in your queue whose status is TODO **AND** whose blockers are all DONE (or IN_REVIEW with API contract stable, for FE module tasks).
3. If your next task is still blocked, run ``node scripts/check-track-status.js`` every ~10 min and wait. Do not start out-of-order.
4. For the picked task, dispatch the standard multi-agent workflow via the manager skill:
   ``Implementation -> Review -> Test -> Documentation``
5. Update task status with ``/task-status TASK-XXX <STATUS>`` after each phase transition.
6. NEVER touch tasks outside your queue -- other dev agents own those.
7. When all tasks in your queue reach DONE, report completion and exit.

## First action
Run ``node scripts/check-track-status.js`` to see current state, then start working on your first available task.
"@
}

# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Parallel Dev Agent Launcher ===" -ForegroundColor Cyan
Write-Host "Workspace: $workspaceRoot"
Write-Host "Tracks   : $($selected -join ', ')"
Write-Host ""

foreach ($name in $selected) {
    if (-not $trackDefs.ContainsKey($name)) {
        Write-Warning "Unknown track '$name' -- skipped. Valid: $($trackDefs.Keys -join ', ')"
        continue
    }

    $track   = $trackDefs[$name]
    $prompt  = Build-Prompt -TrackName $name -Track $track
    $promptB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($prompt))

    Write-Host "[$name] $($track.Title)" -ForegroundColor Yellow
    Write-Host "       Queue: $($track.Queue)"

    if ($DryRun) {
        Write-Host "       (dry-run -- no window opened)" -ForegroundColor DarkGray
        continue
    }

    # Spawn a new PowerShell window:
    #   1. cd to workspace root
    #   2. set window title
    #   3. decode the prompt and pipe it into `claude`
    $launchCmd = @"
`$Host.UI.RawUI.WindowTitle = '$($track.Title)';
Set-Location '$workspaceRoot';
Write-Host '=== $($track.Title) ===' -ForegroundColor Cyan;
Write-Host 'Queue: $($track.Queue)' -ForegroundColor Yellow;
Write-Host '';
`$prompt = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('$promptB64'));
claude `$prompt
"@

    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $launchCmd
    )

    Start-Sleep -Milliseconds 800   # stagger so spawns do not collide
}

if (-not $DryRun) {
    Write-Host ""
    Write-Host "Launched $($selected.Count) dev agents." -ForegroundColor Green
    Write-Host "Monitor progress: node scripts/check-track-status.js"
    Write-Host "Stop one        : close its PowerShell window"
    Write-Host ""
}
