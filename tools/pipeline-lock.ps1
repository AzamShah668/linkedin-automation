# pipeline-lock.ps1 — one lock, shared by every runner that touches LinkedIn.
#
# Dot-source it, then wrap the real work:
#     . (Join-Path $PSScriptRoot 'pipeline-lock.ps1')
#     if (-not (Enter-PipelineLock -Name 'discovery' -Log $log)) { exit 0 }
#     try { ...the real work... } finally { Exit-PipelineLock }
#
# WHY THIS EXISTS (2026-07-31). Every runner already had a guard that skipped when a
# LinkedIn MCP server was running. That guard is useless in the case that actually
# happens: the laptop sleeps through the day, Windows fires ALL the missed tasks at
# once on wake, and at that instant no server exists yet — so all five pass the guard,
# then start four servers that fight over one browser profile. Observed 2026-07-31
# 22:01: five tasks launched within 3 seconds, 4 MCP servers alive at once, nothing
# useful accomplished.
#
# A "is anyone else running?" check is a race. A lock is not: acquisition is atomic,
# so exactly one runner wins and the rest step aside.

$script:PipelineLockPath   = Join-Path $PSScriptRoot '..\output\.pipeline.lock'
$script:PipelineLockHandle = $null

# A crashed run must not wedge the pipeline forever, so a lock whose owner is gone is
# stealable. Time alone is not the test — a legitimately slow discovery run can exceed
# any threshold — so the owning PID is checked first and the age is only the backstop.
$script:PipelineLockMaxAgeMinutes = 90

function Enter-PipelineLock {
    param(
        [Parameter(Mandatory)][string]$Name,
        [string]$Log,
        [int]$WaitSeconds = 0        # 0 = give up immediately; the task will run again later
    )

    $dir = Split-Path $script:PipelineLockPath -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

    $deadline = (Get-Date).AddSeconds($WaitSeconds)
    do {
        Remove-StalePipelineLock -Log $Log

        try {
            # CreateNew is atomic: it throws if the file already exists. Holding the
            # handle open for the life of the run is what makes the lock real - a lock
            # you write and close is just a note.
            # FileShare::ReadWrite, NOT ::Read. Exclusivity comes from CreateNew (which
            # throws if the file exists), so the share mode only governs whether anyone
            # can INSPECT the lock while it is held. With ::Read, a second process's
            # ReadAllText threw a sharing violation, so it could never see the owning pid
            # or the age - it just knew "something is there". That turned a wedged run
            # into a permanently blocked pipeline (seen 2026-08-01 04:38: a reply check
            # stuck since 02:12 held the lock and nothing could diagnose or clear it).
            $script:PipelineLockHandle = [System.IO.File]::Open(
                $script:PipelineLockPath,
                [System.IO.FileMode]::CreateNew,
                [System.IO.FileAccess]::Write,
                [System.IO.FileShare]::ReadWrite)

            $stamp = "$PID|$Name|$((Get-Date).ToString('o'))"
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($stamp)
            $script:PipelineLockHandle.Write($bytes, 0, $bytes.Length)
            $script:PipelineLockHandle.Flush()
            Write-LockLine "$Name acquired the pipeline lock (pid $PID)." $Log
            return $true
        }
        catch {
            # Deliberately untyped. PowerShell wraps a .NET method failure in a
            # MethodInvocationException, so `catch [System.IO.IOException]` can slip
            # past and let the failure escape the function entirely. Any failure to
            # create the file means somebody else holds it, which is all we need.
            if ((Get-Date) -lt $deadline) { Start-Sleep -Seconds 5; continue }
            $owner = Get-PipelineLockOwner
            Write-LockLine "SKIPPED: $Name could not get the pipeline lock; $owner is using it. Not an error - this run stands down and the next scheduled cycle picks it up." $Log
            return $false
        }
    } while ((Get-Date) -lt $deadline)

    return $false
}

function Exit-PipelineLock {
    if ($script:PipelineLockHandle) {
        try { $script:PipelineLockHandle.Close(); $script:PipelineLockHandle.Dispose() } catch {}
        $script:PipelineLockHandle = $null
    }
    try { Remove-Item $script:PipelineLockPath -Force -ErrorAction SilentlyContinue } catch {}
}

function Read-PipelineLockText {
    # MUST open with FileShare::ReadWrite. File.ReadAllText requests FileShare::Read,
    # which forbids the holder's existing WRITE handle, so it throws a sharing violation
    # on a perfectly healthy lock. Both sides of a share negotiation have to permit the
    # other's access - getting only the writer's side right (as the first fix did) still
    # left the lock undiagnosable while held.
    $fs = [System.IO.File]::Open(
        $script:PipelineLockPath,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::ReadWrite)
    try {
        $sr = New-Object System.IO.StreamReader($fs)
        try { return $sr.ReadToEnd() } finally { $sr.Dispose() }
    } finally { $fs.Dispose() }
}

function Get-PipelineLockOwner {
    try {
        $raw = Read-PipelineLockText
        $lockPid, $name, $when = $raw.Split('|')
        return "$name (pid $lockPid, since $when)"
    } catch { return 'another run' }
}

function Remove-StalePipelineLock {
    param([string]$Log)
    if (-not (Test-Path $script:PipelineLockPath)) { return }

    $lockPid = $null; $name = 'unknown'; $started = $null
    try {
        $raw = Read-PipelineLockText
        $lockPid, $name, $when = $raw.Split('|')
        $started = [datetime]::Parse($when)
    } catch {
        # UNREADABLE IS NOT THE SAME AS ABANDONED, and getting this backwards defeated
        # the entire lock (caught in testing 2026-07-31). The holder keeps the file open
        # for write, so a second process's ReadAllText throws a sharing violation - which
        # is proof the lock is ALIVE, not proof it is garbage. Deleting here let the
        # second runner walk straight in.
        # So: refuse by default, and only clear if the file has also gone stale by age,
        # which is the one case where it really is abandoned rubbish we cannot parse.
        $age = (Get-Date) - (Get-Item $script:PipelineLockPath).LastWriteTime
        if ($age.TotalMinutes -gt $script:PipelineLockMaxAgeMinutes) {
            Write-LockLine "clearing an unreadable pipeline lock last written $([int]$age.TotalMinutes) min ago." $Log
            Remove-Item $script:PipelineLockPath -Force -ErrorAction SilentlyContinue
        }
        return
    }

    $alive = $false
    if ($lockPid) { $alive = [bool](Get-Process -Id $lockPid -ErrorAction SilentlyContinue) }

    if (-not $alive) {
        Write-LockLine "clearing a stale pipeline lock from $name (pid $lockPid is gone - that run died without releasing it)." $Log
        Remove-Item $script:PipelineLockPath -Force -ErrorAction SilentlyContinue
        return
    }

    if ($started -and ((Get-Date) - $started).TotalMinutes -gt $script:PipelineLockMaxAgeMinutes) {
        # The owner is ALIVE but has been holding the lock for hours. A run that long
        # is wedged, not busy: the real runners finish in 2-10 minutes. Deleting the
        # file alone does not work while the owner holds the handle open, so the wedged
        # process has to go too, or the whole pipeline stays blocked indefinitely.
        # Only ever applied past the age threshold, and always logged loudly.
        Write-LockLine "WEDGED: $name (pid $lockPid) has held the pipeline lock for over $script:PipelineLockMaxAgeMinutes minutes. Killing it so the pipeline can proceed." $Log
        try {
            Stop-Process -Id $lockPid -Force -ErrorAction Stop
            Start-Sleep -Seconds 2
        } catch {
            Write-LockLine "could not kill pid $lockPid : $($_.Exception.Message)" $Log
        }
        # Its children (claude.exe) outlive the parent and keep the handle, so clear the
        # whole subtree rather than just the script process.
        Get-CimInstance Win32_Process -Filter "ParentProcessId=$lockPid" -ErrorAction SilentlyContinue |
            ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} }
        Remove-Item $script:PipelineLockPath -Force -ErrorAction SilentlyContinue
    }
}

function Write-LockLine {
    param([string]$Message, [string]$Log)
    $line = "$(Get-Date -Format o)  $Message"
    # MUST NOT be Write-Output. These functions return a boolean the callers branch on,
    # and anything written to the output stream is returned ALONGSIDE it: the caller then
    # receives @(logline, $false), a two-element array, which PowerShell evaluates as
    # TRUE. That made Enter-PipelineLock answer "no" while every caller read "yes", so
    # the lock excluded nobody. Caught only because the exclusion test was actually run
    # rather than assumed. Write-Host stays off the output stream; the log file is the
    # durable record either way.
    Write-Host $line
    if ($Log) { $line | Out-File -FilePath $Log -Append -Encoding utf8 }
}
