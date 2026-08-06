# run-pipeline.ps1 — run the whole pipeline once, in the right order, one step at a time.
#
#     powershell -ExecutionPolicy Bypass -File tools/run-pipeline.ps1
#     powershell -ExecutionPolicy Bypass -File tools/run-pipeline.ps1 -Only accepts
#     powershell -ExecutionPolicy Bypass -File tools/run-pipeline.ps1 -SkipDiscoveryIfRanToday:$false
#
# WHY (2026-07-31). Windows already re-runs missed tasks on wake (StartWhenAvailable),
# and that is exactly the problem: after the laptop slept through a day, ALL FIVE fired
# within three seconds, started four LinkedIn MCP servers, and fought over one browser
# profile. Catch-up was never broken; ORDERING was missing.
#
# So: one task on resume/logon runs this, and this runs the steps sequentially in
# priority order. Time-sensitive sends go first, the backlog sweep goes last. Each
# runner still takes the shared pipeline lock, so this is safe even if a normal
# scheduled trigger fires at the same moment - one of them simply stands down.

param(
  [ValidateSet('all','accepts','flush','replies','discovery','packets')]
  [string]$Only = 'all',
  [bool]$SkipDiscoveryIfRanToday = $true,
  [int]$PacketMax = 2
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

Say "=== run-pipeline start (only=$Only) $(Get-Date -Format o) ==="

# Ordered deliberately. Anything that puts a message in front of a person runs FIRST,
# because those are the steps with a deadline; discovery and packet-building are work
# that keeps. A crash in a later step must never cost an overdue pitch.
$steps = @(
  @{ key='accepts';   name='Watch Accepts (stage 2 sends)'; script='watch-accepts.ps1';  args=@() },
  @{ key='flush';     name='Flush Approved (stage 1 sends)'; script='flush-approved.ps1'; args=@() },
  @{ key='replies';   name='Reply Check';                    script='check-replies.ps1';  args=@() },
  @{ key='discovery'; name='Daily Discovery';                script='daily-discovery.ps1';args=@() },
  @{ key='packets';   name='Sweep Packets';                  script='sweep-packets.ps1';  args=@('-Max', "$PacketMax") }
)

foreach ($step in $steps) {
  if ($Only -ne 'all' -and $Only -ne $step.key) { continue }

  # Discovery is the one step that is genuinely once-a-day. Without this, every wake
  # would re-run a 10-minute LinkedIn search and re-add the same jobs.
  if ($step.key -eq 'discovery' -and $SkipDiscoveryIfRanToday -and $Only -eq 'all') {
    # Match the END marker, not the start header. A run that was killed mid-flight
    # (exactly what happened at 22:01 tonight) leaves a header behind, and matching on
    # that would count a stampede casualty as "discovery already happened today" and
    # skip it for the rest of the day. Started is not finished.
    $today = Join-Path $proj ("output\discovery-log\{0:yyyy-MM-dd}.log" -f (Get-Date))
    if ((Test-Path $today) -and (Select-String -Path $today -Pattern '=== end \(exit' -Quiet)) {
      Say "SKIP  $($step.name): already completed today. Use -SkipDiscoveryIfRanToday `$false to force it."
      continue
    }
  }

  $path = Join-Path $proj "tools\$($step.script)"
  if (-not (Test-Path $path)) { Say "SKIP  $($step.name): $($step.script) not found."; continue }

  Say "---- $($step.name) ----"
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  & powershell -NoProfile -ExecutionPolicy Bypass -File $path @($step.args) 2>&1 |
    ForEach-Object { $line = "      $_"; Write-Output $line; $line | Out-File -FilePath $log -Append -Encoding utf8 }
  $sw.Stop()
  Say "---- $($step.name) finished in $([int]$sw.Elapsed.TotalSeconds)s (exit $LASTEXITCODE)"
}

Say "=== run-pipeline end $(Get-Date -Format o) ==="
Say "Judge this by the individual runner logs, not by this file or an exit code."
exit 0
