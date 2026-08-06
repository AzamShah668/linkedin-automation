# auto-apply.ps1 — take a built packet and actually SUBMIT the application.
#     powershell -ExecutionPolicy Bypass -File tools/auto-apply.ps1 -JobId <notion-page-id>
#     powershell -ExecutionPolicy Bypass -File tools/auto-apply.ps1 -All
#
# Runs Claude headless against docs/knowledge/17-auto-apply-runbook.md, driving the
# Playwright MCP over LINKEDIN EASY APPLY (external ATS is the fallback, not the target).
#
# THIS ONE SENDS. It is the only runner in this project that completes an irreversible
# action with no human tick — owner decision D16, deliberately.
#
# Retargeted 2026-07-30 (D18): this used to drive external ATS only and skipped every
# Easy-Apply role. Since the board is populated from LinkedIn search, that meant it
# skipped nearly everything. Easy Apply is now the primary path.

param(
  [string]$JobId,
  [switch]$All,
  [int]$Max = 5
)

if (-not $JobId -and -not $All) {
  Write-Output "Give either -JobId <notion-page-id> or -All. Refusing to guess which job to apply to."
  exit 1
}

$ErrorActionPreference = 'Continue'
$proj = 'd:\linkdin automation'
Set-Location $proj

# claude.exe emits UTF-16 to the console; force UTF-8 or the log is unreadable.
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; chcp 65001 > $null } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $proj 'output\apply-log'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("{0:yyyy-MM-dd}-apply.log" -f (Get-Date))
$claude = Join-Path $env:USERPROFILE '.local\bin\claude.exe'

$target = if ($All) { "ALL rows at status To Apply (max $Max)" } else { $JobId }
"=== auto-apply $target  $(Get-Date -Format o) ===" | Out-File -FilePath $log -Append -Encoding utf8

# Guard 1: the answer bank must exist. Without it there is no legal source of field
# values, and a run would either fill nothing or start inventing — the exact failure
# the bank was created to prevent (D15).
$bank = Join-Path $proj 'profile\application-answers.json'
if (-not (Test-Path $bank)) {
  $msg = "ABORT: profile\application-answers.json is missing. That file is the ONLY legal source of form values; without it nothing may be typed into an employer's form."
  Write-Output $msg; $msg | Out-File -FilePath $log -Append -Encoding utf8
  exit 1
}

# Guard 2: a single job must exist on the board AND have a built packet with a real PDF.
# Applying without one would attach the generic CV instead of the tailored PDF, which
# defeats the whole pipeline.
if ($JobId) {
  $row = & py -3 -c @"
import sys; sys.path.insert(0,'tools')
from board_db import connect, all_rows
hit = [r for r in all_rows(connect()) if r['id'] == '$JobId']
print(f\"{hit[0]['company']} | {hit[0]['job']} | {hit[0].get('status','?')}\" if hit else '')
"@ | Out-String
  $row = $row.Trim()
  if (-not $row) {
    $msg = "ABORT: no board row with id $JobId."
    Write-Output $msg; $msg | Out-File -FilePath $log -Append -Encoding utf8
    exit 1
  }
  Write-Output "Target: $row"
  "target: $row" | Out-File -FilePath $log -Append -Encoding utf8

  # The packet is discovered by job_id, the same way the dashboard discovers it, so a
  # newly built packet needs no edit here.
  $packet = & py -3 -c @"
import json, glob
for p in glob.glob('output/outreach/*/packet.json'):
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception:
        continue
    if d.get('job_id') == '$JobId':
        print(f\"{d.get('slug','')}|{d.get('cv_stem','')}\"); break
"@ | Out-String
  $packet = $packet.Trim()
  if (-not $packet) {
    $msg = "ABORT: no packet.json for job $JobId. Build it first (tools/build-packet.ps1 -JobId $JobId); this runner never applies with the generic CV."
    Write-Output $msg; $msg | Out-File -FilePath $log -Append -Encoding utf8
    exit 1
  }
  $slug, $cvStem = $packet.Split('|')
  $pdf = Join-Path $proj "output\pdf\$cvStem.pdf"
  if (-not (Test-Path $pdf)) {
    $msg = "ABORT: packet '$slug' names cv_stem '$cvStem' but output\pdf\$cvStem.pdf does not exist. No tailored PDF, no application."
    Write-Output $msg; $msg | Out-File -FilePath $log -Append -Encoding utf8
    exit 1
  }
  Write-Output "Packet: $slug  ->  $cvStem.pdf"
  "packet: $slug -> $cvStem.pdf" | Out-File -FilePath $log -Append -Encoding utf8
}

# Guard 3: PROFILE CONTENTION.
# 3a — another Claude window means another LinkedIn MCP server, and a contended machine
# misreports everything as "session expired" (D13). This runner does not itself use the
# LinkedIn MCP, but a second Claude session competing for the same machine is still the
# single most common cause of a silently useless run.
$holder = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -like '*linkedin-mcp*profile*' }
if ($holder) {
  $msg = "SKIPPED: the LinkedIn browser profile is held by another process (pid $($holder[0].ProcessId)). Close other Claude Code windows and run this again."
  Write-Output $msg; $msg | Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

# Count python-only: each Claude session spawns one server plus two uvx wrappers, so
# counting the whole tree over-reports 3x and would refuse every run.
$servers = @(Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
             Where-Object { $_.CommandLine -like '*mcp-server-linkedin*' })
if ($servers.Count -ge 1) {
  $pids = ($servers | ForEach-Object { $_.ProcessId }) -join ', '
  $msg = @"
SKIPPED: $($servers.Count) LinkedIn MCP server(s) already running (pid $pids).
Close every other Claude Code window, then run this again.
Run tools\linkedin-doctor.cmd to confirm nothing is left over.
"@
  Write-Output $msg; $msg | Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

# 3b — the Playwright profile. THIS run needs .pw_browser for itself: it is where the
# LinkedIn login lives and where the PDF gets attached from. A second Chromium on the
# same directory fails in a way that reads like a broken site rather than a locked
# profile — the same class of bug as D13, different directory.
$pw = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -like '*.pw_browser*' }
if ($pw) {
  $msg = "SKIPPED: the Playwright profile .pw_browser is held by another process (pid $($pw[0].ProcessId)). Close it and run again."
  Write-Output $msg; $msg | Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

$scope = if ($All) {
  "EVERY board row whose status is 'To Apply' and which has a built packet, in fit order, highest first. Stop after $Max applications and report the rest as remaining."
} else {
  "the board row with Notion page id $JobId."
}

$prompt = @"
Submit the real job application(s) for $scope
Follow docs/knowledge/17-auto-apply-runbook.md EXACTLY. Read that runbook and
docs/knowledge/07-current-state.md FIRST, then work the steps in order.

THIS RUN SUBMITS. That is intended (decision D16). No Slack approval, no waiting.

The target is LINKEDIN EASY APPLY, driven with the Playwright MCP in the .pw_browser
profile. External ATS is only the fallback when a role has no Easy Apply button.

Non-negotiables:
- FIRST navigate to linkedin.com/feed and snapshot. If it shows a sign-in page, STOP the
  whole run and report 'linkedin-logged-out'. Never attempt a login from this run.
- ONLY values from profile/application-answers.json may be typed into an employer's form.
  Never infer, never guess, never fill a number because the form insists. A null in the
  NEEDS_AZAM block means LEAVE THE FIELD BLANK. The single permitted derivation is
  'how did you hear about us' -> LinkedIn, because that is where these roles came from.
- NUMERIC FIELDS REJECT WORDS (proven, do not rediscover): notice period must be typed as
  0, NOT 'Immediate'; expected CTC must be 840000 for India, NOT '8.4'; 30000 for
  international. After correcting either one, RE-SNAPSHOT: LinkedIn reveals extra Yes/No
  questions that were hidden behind the failing field.
- Easy Apply is a multi-step wizard. Snapshot, fill, click Next, snapshot again and verify
  the step actually advanced. Never click Next twice without a snapshot in between.
- Field required AND no answer-bank value -> DO NOT SUBMIT. Set status
  'Blocked - needs answer', append the field name to output/apply-log/needs-answer.md,
  and move to the next job. Never stop and wait for a human.
- Attach the TAILORED pdf named in the packet's cv_stem (output/pdf/<cv_stem>.pdf) by
  choosing 'Upload resume'. LinkedIn pre-fills the LAST resume used; that is the wrong
  one. Verify in a snapshot that the shown filename is <cv_stem>.pdf before submitting.
- Verify with a second snapshot BEFORE clicking Submit; any mismatch means do not submit.
- NEVER resubmit anything. One attempt per company per role, ever. Recro (Generative AI
  Engineer) was already submitted 2026-07-29 - never attempt it again.
- If LinkedIn already shows 'Applied' for a role, log 'already-applied', set the status,
  and move on.
- CAPTCHA, login wall, or an assessment test -> log the reason, skip the job, move on.
- Never use browser_run_code_unsafe or browser_evaluate on an employer's form.
- Screenshot receipt to output/apply-log/<slug>-<date>.png after each submit, set status
  in the mirror, then py -3 tools/notion_push.py.
- Randomised 40-180s gap between applications.

Report at the end, per job: company, role, SUBMITTED / BLOCKED / SKIPPED, the reason if not
submitted, and any field that needs Azam to fill in the answer bank.
"@

& $claude -p $prompt --permission-mode default 2>&1 |
  Out-File -FilePath $log -Append -Encoding utf8

$code = $LASTEXITCODE
"=== end (exit $code) $(Get-Date -Format o) ===" | Out-File -FilePath $log -Append -Encoding utf8

Get-Content -Path $log -Tail 60 -Encoding utf8 | ForEach-Object { Write-Output $_ }
exit $code
