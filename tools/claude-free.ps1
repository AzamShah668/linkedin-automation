# claude-free.ps1 - launch a Claude Code session routed through the local OmniRoute
# gateway (free/pooled models) INSTEAD of the Opus 5 subscription.
#
# Why a launcher and not an env var:
#   Setting ANTHROPIC_BASE_URL globally would reroute EVERY Claude Code session,
#   including cv.py's headless packet build - the one artifact a human reads (D26/D27).
#   That is the exact silent-degradation shape this project keeps getting bitten by.
#   So the free path is opt-in, per session, and announces itself.
#
# Uses OmniRoute's own `launch`, which resolves the base URL + token from the active
# context, health-checks the server, and execs `claude`. See docs/knowledge/29-omniroute-gateway.md.

[CmdletBinding()]
param(
    # Model profile written by `omniroute setup-claude` (e.g. glm52, kimi-k27).
    # Omit to use OmniRoute's auto-routing.
    # NOT named -Profile: that shadows PowerShell's $PROFILE automatic variable.
    [string]$ModelProfile,

    # Everything else is passed straight through to `omniroute launch`.
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Passthrough
)

$ErrorActionPreference = 'Stop'

$GatewayUrl = 'http://localhost:20128'

function Fail($message, $hint) {
    Write-Host ''
    Write-Host "  BLOCKED  $message" -ForegroundColor Red
    if ($hint) {
        Write-Host "           $hint" -ForegroundColor Yellow
    }
    Write-Host ''
    exit 1
}

# --- 1. Is OmniRoute installed at all? -------------------------------------------------
# Resolve by PATH first, then by npm's global bin. Measured 2026-08-13: the shim exists at
# %APPDATA%\npm but that directory is missing from some shells' PATH, so a PATH-only check
# reports "not installed" for a package that is installed. Same disease as D24 - never
# conclude from one shell.
$omniExe = $null
$onPath = Get-Command omniroute -ErrorAction SilentlyContinue
if ($onPath) {
    $omniExe = 'omniroute'
} else {
    $globalBin = $null
    try { $globalBin = (& npm prefix -g).Trim() } catch { }
    if ($globalBin) {
        $candidate = Join-Path $globalBin 'omniroute.cmd'
        if (Test-Path $candidate) { $omniExe = $candidate }
    }
}
if (-not $omniExe) {
    Fail 'omniroute is not installed (not on PATH, not in npm''s global bin).' 'Run:  npm install -g omniroute'
}

# --- 2. Is the gateway actually up? ----------------------------------------------------
# Launching Claude Code at a dead gateway produces a confusing connection error several
# layers down. Check here, where the message can say what to do about it.
$up = $false
try {
    Invoke-WebRequest -Uri $GatewayUrl -UseBasicParsing -TimeoutSec 5 | Out-Null
    $up = $true
} catch {
    # A 4xx still proves something is listening; only a transport failure means it is down.
    if ($_.Exception.Response) { $up = $true }
}
if (-not $up) {
    Fail "nothing is listening on $GatewayUrl." 'Start the gateway in another terminal:  omniroute'
}

# --- 3. Has anything permanently rerouted the DEFAULT session? -------------------------
# If this trips, plain `claude` is silently on free models too and the CV engine is
# no longer Opus 5. That is a correctness problem, not a preference.
$defaultSettings = Join-Path $env:USERPROFILE '.claude\settings.json'
if (Test-Path $defaultSettings) {
    $raw = Get-Content $defaultSettings -Raw
    if ($raw -match 'ANTHROPIC_BASE_URL') {
        Write-Host ''
        Write-Host '  WARNING  ~/.claude/settings.json contains ANTHROPIC_BASE_URL.' -ForegroundColor Yellow
        Write-Host '           Your DEFAULT `claude` sessions are routed through a gateway too,' -ForegroundColor Yellow
        Write-Host '           which means cv.py builds CVs on a free model. Remove it to restore' -ForegroundColor Yellow
        Write-Host '           the subscription as the default.' -ForegroundColor Yellow
    }
}
foreach ($scope in @('User', 'Machine')) {
    $persisted = [Environment]::GetEnvironmentVariable('ANTHROPIC_BASE_URL', $scope)
    if ($persisted) {
        Write-Host ''
        Write-Host "  WARNING  ANTHROPIC_BASE_URL is set permanently at $scope scope ($persisted)." -ForegroundColor Yellow
        Write-Host '           Every Claude Code session is rerouted, not just this one.' -ForegroundColor Yellow
    }
}

# --- 4. Say plainly which engine is about to answer ------------------------------------
if ($ModelProfile) { $engine = "profile '$ModelProfile'" } else { $engine = 'auto-routing' }
Write-Host ''
Write-Host '  == FREE MODELS ==================================================' -ForegroundColor Cyan
Write-Host "  This session runs on OmniRoute ($engine), NOT Opus 5." -ForegroundColor Cyan
Write-Host '  Do NOT build a tailored CV here - a human reads that one (D26/D27).' -ForegroundColor Cyan
Write-Host '  Close this session and run `claude` for subscription-quality work.' -ForegroundColor Cyan
Write-Host '  =================================================================' -ForegroundColor Cyan
Write-Host ''

# --- 5. Hand off to OmniRoute ----------------------------------------------------------
$launchArgs = @('launch')
if ($ModelProfile) { $launchArgs += @('--profile', $ModelProfile) }
if ($Passthrough) { $launchArgs += $Passthrough }

& $omniExe @launchArgs
exit $LASTEXITCODE
