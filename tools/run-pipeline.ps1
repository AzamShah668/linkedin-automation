# run-pipeline.ps1 — run the WHOLE pipeline once, in the right order, one step at a time.
#
#     powershell -ExecutionPolicy Bypass -File tools/run-pipeline.ps1
#     powershell -ExecutionPolicy Bypass -File tools/run-pipeline.ps1 -Only outreach
#     powershell -ExecutionPolicy Bypass -File tools/run-pipeline.ps1 -WhatIf
#
# WHY (2026-07-31). Windows already re-runs missed tasks on wake (StartWhenAvailable),
# and that is exactly the problem: after the laptop slept through a day, ALL FIVE fired
# within three seconds, started four LinkedIn MCP servers, and fought over one browser
# profile. Catch-up was never broken; ORDERING was missing.
#
# WHY IT GREW (2026-08-15). The pipeline could apply to 21 jobs in an evening and 19 of them
# reached no human, because the half that turns an application into a conversation — find the
# recruiter, ask for the tick, send the invite, chase the silence — existed only as runbooks a
# person read by hand. Applying was never the bottleneck; it was just the visible one.
#
# The full loop is now:
#
#   accepts -> flush -> replies -> nudge -> discovery -> apply -> outreach -> packets
#   \___ deliver what is owed ___/  \_ chase _/  \____ create new work ____/  \_ prepare _/
#
# Anything that puts a message in front of a person runs FIRST, because those steps have a
# deadline. Discovery, applying and packet-building are work that keeps. A crash late in the
# list must never cost an overdue pitch.

param(
  [ValidateSet('all','accepts','flush','replies','nudge','discovery','apply','outreach','packets')]
  [string]$Only = 'all',
  [bool]$SkipDiscoveryIfRanToday = $true,
  [int]$PacketMax = 2,
  # How many Easy Apply submissions one pipeline run may make. Deliberately well under a day's
  # capacity: the throttle inside apply-all is the ban-safety mechanism and this is the second one.
  [int]$ApplyMax = 8,
  # How many companies to research per run. Search is the endpoint LinkedIn rate-limits hardest.
  [int]$OutreachMax = 5,
  [switch]$WhatIf
)

$ErrorActionPreference = 'Continue'
$proj = 'd:\linkdin automation'
Set-Location $proj

try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; chcp 65001 > $null } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $proj 'output\pipeline-log'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("{0:yyyy-MM-dd}-pipeline.log" -f (Get-Date))

function Say($msg) {
  $line = "$(Get-Date -Format 'HH:mm:ss')  $msg"
  Write-Output $line
  $line | Out-File -FilePath $log -Append -Encoding utf8
}

. (Join-Path $PSScriptRoot 'pipeline-lock.ps1')

# ---------------------------------------------------------------------------------------------
# ONE browser profile, three steps that need it.
#
# `replies`, `apply` and `outreach` all drive .pw_browser\linkedin_user_data, and Chromium allows
# exactly one process per profile — a second launch dies with "Failed to create a ProcessSingleton",
# exit code 21. Observed on 2026-08-15: an outreach run that finished cleanly still left sixteen
# chrome.exe processes holding the profile, and the next Playwright step could not start at all.
#
# Steps here run strictly sequentially, so at this point in the script nothing of ours should hold
# the profile and anything that does is a leak from a previous step.
#
# ⚠️ It will NOT kill a profile held while an interactive Claude Code session has a browser open —
# that is a live window someone is using, and killing it loses their state. Skipping the step is
# recoverable; killing a person's browser is not.
# ---------------------------------------------------------------------------------------------
function Release-BrowserProfile {
  param([int]$WaitSeconds = 6)

  $mcp = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
         Where-Object { $_.CommandLine -like '*linkedin-mcp*profile*' }
  if ($mcp) {
    Say "  profile held by an interactive LinkedIn MCP session (pid $($mcp[0].ProcessId)); NOT killing it"
    return $false
  }

  $held = @(Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like '*linkedin_user_data*' })
  if ($held.Count -eq 0) { return $true }

  Say "  releasing browser profile: $($held.Count) leaked chrome process(es) from an earlier step"
  foreach ($p in $held) { try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } catch {} }
  Start-Sleep -Seconds $WaitSeconds

  $left = @(Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like '*linkedin_user_data*' })
  if ($left.Count -gt 0) {
    Say "  !! $($left.Count) chrome process(es) still hold the profile; this step will likely exit 21"
    return $false
  }
  return $true
}

# Discovery is genuinely once-a-day; so is a full apply batch. Both are gated on an END marker in
# today's log, never a start header: a run killed mid-flight leaves a header behind, and matching
# on that counts a stampede casualty as "already done" and skips it for the rest of the day.
function Test-RanToday {
  param([string]$Path, [string]$EndPattern)
  if (-not (Test-Path $Path)) { return $false }
  return [bool](Select-String -Path $Path -Pattern $EndPattern -Quiet)
}

$applyMarker = Join-Path $logDir ("{0:yyyy-MM-dd}-apply.done" -f (Get-Date))

# key       : -Only selector
# name      : what appears in the log
# script    : a tools\*.ps1 runner (takes the pipeline lock itself)
# cmd/args  : a python module run directly (this script takes the lock for it)
# browser   : needs the Playwright profile released first
$steps = @(
  @{ key='accepts';   name='Watch Accepts (stage 2 sends)';  script='watch-accepts.ps1';  args=@() },
  @{ key='flush';     name='Flush Approved (stage 1 sends)'; script='flush-approved.ps1'; args=@() },
  @{ key='replies';   name='Reply Check';                    script='check-replies.ps1';  args=@(); browser=$true },
  @{ key='nudge';     name='Follow-ups Due';                 cmd='apps.autopilot.nudge';    args=@('--notify') },
  @{ key='discovery'; name='Daily Discovery';                script='daily-discovery.ps1';args=@() },
  @{ key='apply';     name='Apply (Easy Apply batch)';       cmd='apps.autopilot.run';
     args=@('apply-all','--limit',"$ApplyMax",'--max-per-company','1'); browser=$true; onceADay=$true },
  @{ key='outreach';  name='Find a human + CONNECT';         cmd='apps.autopilot.outreach';
     args=@('--limit',"$OutreachMax"); browser=$true },
  @{ key='packets';   name='Sweep Packets';                  script='sweep-packets.ps1';  args=@('-Max', "$PacketMax") }
)

Say "=== run-pipeline start (only=$Only) $(Get-Date -Format o) ==="
if ($WhatIf) { Say "WHATIF: listing steps only, running nothing." }

foreach ($step in $steps) {
  if ($Only -ne 'all' -and $Only -ne $step.key) { continue }

  if ($WhatIf) {
    if ($step.script) { Say "WOULD RUN  $($step.name)  ->  tools\$($step.script) $($step.args -join ' ')" }
    else              { Say "WOULD RUN  $($step.name)  ->  py -3 -u -m $($step.cmd) $($step.args -join ' ')" }
    continue
  }

  # --- once-a-day gates -------------------------------------------------------------------
  if ($step.key -eq 'discovery' -and $SkipDiscoveryIfRanToday -and $Only -eq 'all') {
    $today = Join-Path $proj ("output\discovery-log\{0:yyyy-MM-dd}.log" -f (Get-Date))
    if (Test-RanToday -Path $today -EndPattern '=== end \(exit') {
      Say "SKIP  $($step.name): already completed today. Use -SkipDiscoveryIfRanToday `$false to force it."
      continue
    }
  }
  if ($step.onceADay -and $Only -eq 'all' -and (Test-Path $applyMarker)) {
    Say "SKIP  $($step.name): already ran today. Run with -Only apply to force it."
    continue
  }

  if ($step.browser) {
    if (-not (Release-BrowserProfile)) {
      Say "SKIP  $($step.name): browser profile is not available."
      continue
    }
  }

  Say "---- $($step.name) ----"
  $sw = [System.Diagnostics.Stopwatch]::StartNew()

  if ($step.script) {
    # These runners take the pipeline lock themselves.
    $path = Join-Path $proj "tools\$($step.script)"
    if (-not (Test-Path $path)) { Say "SKIP  $($step.name): $($step.script) not found."; continue }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $path @($step.args) 2>&1 |
      ForEach-Object { $line = "      $_"; Write-Output $line; $line | Out-File -FilePath $log -Append -Encoding utf8 }
  }
  else {
    # A python step has no lock of its own, so take it here. Without this, a 4-hourly
    # watch-accepts trigger could fire into the middle of an apply batch and both would
    # reach for the same browser profile.
    if (-not (Enter-PipelineLock -Name $step.key -Log $log)) {
      Say "SKIP  $($step.name): another pipeline step holds the lock."
      continue
    }
    try {
      # -u or python buffers and the log sits empty while you wonder whether it died.
      & py -3 -u -m $step.cmd @($step.args) 2>&1 |
        ForEach-Object { $line = "      $_"; Write-Output $line; $line | Out-File -FilePath $log -Append -Encoding utf8 }
      if ($step.onceADay -and $LASTEXITCODE -eq 0) { Get-Date -Format o | Out-File -FilePath $applyMarker -Encoding utf8 }
    }
    finally { Exit-PipelineLock }
  }

  $sw.Stop()
  Say "---- $($step.name) finished in $([int]$sw.Elapsed.TotalSeconds)s (exit $LASTEXITCODE)"
}

Say "=== run-pipeline end $(Get-Date -Format o) ==="
Say "Judge this by the individual runner logs, not by this file or an exit code."
exit 0
