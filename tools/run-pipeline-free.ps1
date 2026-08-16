# run-pipeline-free.ps1 — the whole pipeline on OmniRoute, with no Claude Code anywhere.
#
#     powershell -ExecutionPolicy Bypass -File tools/run-pipeline-free.ps1
#     ... -Only outreach
#     ... -WhatIf
#
# ⚠️ THIS DOES NOT REPLACE tools/run-pipeline.ps1. Azam's instruction, 2026-08-16: "I don't want
# you to replace all this ... the previous one with the cloud agents should be there. It should
# not get deleted." The Claude stack keeps its runner, its scheduled task and its behaviour; this
# is a second entry point that happens to need no Claude.
#
#   pipeline.cmd       -> run-pipeline.ps1       Claude stack     scheduled daily 10:30
#   pipeline-free.cmd  -> THIS                   OmniRoute stack  unscheduled, run by hand
#
# Ordering is identical and for the same reason (D20): anything that puts a message in front of a
# person runs FIRST, because only those steps have a deadline. Discovery, applying and CV building
# are work that keeps, and a crash late must never cost an overdue pitch.

param(
  [ValidateSet('all','accepts','dm','replies','gmail','nudge','discovery','intake','apply','outreach','cv')]
  [string]$Only = 'all',
  [int]$ApplyMax = 8,
  [int]$OutreachMax = 5,
  [int]$DiscoverPages = 2,
  [int]$CvMax = 2,
  [switch]$WhatIf
)

$ErrorActionPreference = 'Continue'
$proj = 'd:\linkdin automation'
Set-Location $proj

try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; chcp 65001 > $null } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONPATH = $proj

$logDir = Join-Path $proj 'output\pipeline-log'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("{0:yyyy-MM-dd}-pipeline-free.log" -f (Get-Date))

function Say($msg) {
  $line = "$(Get-Date -Format 'HH:mm:ss')  $msg"
  Write-Output $line
  $line | Out-File -FilePath $log -Append -Encoding utf8
}

. (Join-Path $PSScriptRoot 'pipeline-lock.ps1')

# Same guard as the Claude runner, and it matters MORE here: this stack has four browser steps
# rather than three. Chromium allows one process per profile, and a leaked one makes the next step
# die with exit 21. It refuses to kill a profile an interactive MCP session holds - skipping a step
# is recoverable, killing someone's open browser is not.
function Release-BrowserProfile {
  $mcp = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
         Where-Object { $_.CommandLine -like '*linkedin-mcp*profile*' }
  if ($mcp) {
    Say "  profile held by an interactive LinkedIn MCP session (pid $($mcp[0].ProcessId)); NOT killing it"
    return $false
  }
  $held = @(Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like '*linkedin_user_data*' })
  if ($held.Count -eq 0) { return $true }
  Say "  releasing browser profile: $($held.Count) leaked chrome process(es)"
  foreach ($p in $held) { try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } catch {} }
  Start-Sleep -Seconds 6
  $left = @(Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like '*linkedin_user_data*' })
  if ($left.Count -gt 0) { Say "  !! $($left.Count) still hold the profile; this step will exit 21"; return $false }
  return $true
}

# module  : python -m target
# browser : needs the single Chromium profile released first
# soft    : a non-zero exit is information, not a failure (Gmail is not set up yet, etc.)
$steps = @(
  @{ key='accepts';   name='Check who accepted';        module='apps.autopilot.accepts';        args=@();                                   browser=$true },
  @{ key='dm';        name='Deliver due pitches';       module='apps.autopilot.free.dm';        args=@('--limit','3');                      browser=$true },
  @{ key='replies';   name='LinkedIn inbox';            module='apps.autopilot.replies';        args=@('--notify');                         browser=$true },
  @{ key='gmail';     name='Gmail inbox';               module='apps.autopilot.free.gmail';     args=@('--notify');                         soft=$true },
  @{ key='nudge';     name='Follow-ups due';            module='apps.autopilot.nudge';          args=@('--notify') },
  @{ key='discovery'; name='Discover (f_AL=true)';      module='apps.autopilot.free.discover';  args=@('--pages',"$DiscoverPages");         browser=$true; soft=$true },
  @{ key='intake';    name='Score and load the board';  module='apps.autopilot.intake';         args=@('--write') },
  @{ key='apply';     name='Apply (Easy Apply batch)';  module='apps.autopilot.run';            args=@('apply-all','--limit',"$ApplyMax",'--max-per-company','1'); browser=$true },
  @{ key='outreach';  name='Find a human + CONNECT';    module='apps.autopilot.outreach';       args=@('--limit',"$OutreachMax");           browser=$true },
  # Last, deliberately: a tailored CV is valuable but never urgent, and it is the slowest step.
  # The free-stack answer to sweep-packets.ps1. -Only cv was in the ValidateSet with no step
  # behind it, so it silently did nothing - an accepted argument that does nothing is the same
  # silent-success failure this project keeps finding.
  @{ key='cv';        name='Build missing CVs';         module='apps.autopilot.free.cv';        args=@('--sweep',"$CvMax") }
)

Say "=== run-pipeline-free start (only=$Only) $(Get-Date -Format o) ==="
Say "OmniRoute stack: no claude.exe is launched by any step below."

foreach ($step in $steps) {
  if ($Only -ne 'all' -and $Only -ne $step.key) { continue }

  if ($WhatIf) {
    Say "WOULD RUN  $($step.name)  ->  py -3 -u -m $($step.module) $($step.args -join ' ')"
    continue
  }

  if ($step.browser) {
    if (-not (Release-BrowserProfile)) { Say "SKIP  $($step.name): browser profile unavailable."; continue }
  }

  if (-not (Enter-PipelineLock -Name "free-$($step.key)" -Log $log)) {
    Say "SKIP  $($step.name): another pipeline step holds the lock."
    continue
  }

  Say "---- $($step.name) ----"
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    # -u or python buffers and the log sits empty while you wonder whether it died.
    & py -3 -u -m $step.module @($step.args) 2>&1 |
      ForEach-Object { $line = "      $_"; Write-Output $line; $line | Out-File -FilePath $log -Append -Encoding utf8 }
    $code = $LASTEXITCODE
  }
  finally { Exit-PipelineLock }
  $sw.Stop()

  $note = ""
  if ($code -ne 0 -and $step.soft) { $note = "  (non-zero is informational for this step)" }
  Say "---- $($step.name) finished in $([int]$sw.Elapsed.TotalSeconds)s (exit $code)$note"
}

Say "=== run-pipeline-free end $(Get-Date -Format o) ==="
Say "Judge this by the step output above, never by this file's exit code."
exit 0
