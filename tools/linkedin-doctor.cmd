@echo off
setlocal enabledelayedexpansion
REM ===================================================================
REM  LinkedIn MCP doctor — run this BEFORE ever believing "session expired".
REM
REM  Learned the hard way on 2026-07-26: a "Session expired or invalid"
REM  error cost two unnecessary LinkedIn logins and an hour of chasing an
REM  auth bug that did not exist. The real cause was THREE mcp-server-linkedin
REM  processes running at once (one per Claude Code session opened that day),
REM  all competing for the single browser profile at
REM  %USERPROFILE%\.linkedin-mcp\profile. The losers get an empty browser and
REM  report it as expired auth.
REM
REM  Order of diagnosis, cheapest first:
REM    1. count server instances      <- the usual culprit
REM    2. check the cookie timestamp  <- proof of the last real login
REM    3. only then consider a login  <- almost never the answer
REM ===================================================================

set "MCPDIR=%USERPROFILE%\.linkedin-mcp"
set "COOKIES=%MCPDIR%\cookies.json"

echo.
echo ============================================
echo   LinkedIn MCP doctor
echo ============================================
echo.

REM --- 1. how many servers are fighting over the profile? -------------
REM  Count python.exe only: each Claude session spawns ONE python server plus
REM  two uvx/uv wrapper processes, so counting the whole tree over-reports 3x.
echo [1] Running LinkedIn MCP servers ^(one per Claude session^):
echo.
powershell -NoProfile -Command ^
  "$s = @(Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | Where-Object { $_.CommandLine -like '*mcp-server-linkedin*' -or $_.CommandLine -like '*linkedin_mcp*' }); if ($s.Count -eq 0) { Write-Output '    none running (a session starts one on demand)'; exit }; $s | Sort-Object CreationDate | ForEach-Object { Write-Output ('    server PID {0,-8} started {1:HH:mm:ss}' -f $_.ProcessId, $_.CreationDate) }; Write-Output ''; if ($s.Count -gt 1) { Write-Output ('    >> WARNING: {0} servers are running at once.' -f $s.Count); Write-Output '    >> They cannot share one browser profile. This is almost'; Write-Output '    >> certainly your bug, NOT expired auth. The losers get an'; Write-Output '    >> empty browser and report it as a dead session.'; Write-Output ''; Write-Output '    >> Fix: close every Claude Code window except the one you are'; Write-Output '    >>      using. To kill the strays now, keeping the newest:'; $keep = ($s | Sort-Object CreationDate | Select-Object -Last 1).ProcessId; $kill = ($s | Where-Object { $_.ProcessId -ne $keep }).ProcessId; Write-Output ('    >>      Stop-Process -Force -Id {0}' -f ($kill -join ',')); Write-Output ('    >>      (keeps PID {0}, the newest)' -f $keep) } else { Write-Output '    OK: exactly one server - no lock fight.' }"

echo.

REM --- 2. when was a login last actually saved? ----------------------
echo [2] Last saved LinkedIn session:
if exist "%COOKIES%" (
  for %%F in ("%COOKIES%") do echo     cookies.json written %%~tF
  echo     ^(this only changes on a real login/refresh - a working session
  echo      can be hours or days old and still be perfectly valid^)
) else (
  echo     NO cookie file - never logged in. A login IS needed.
)
echo.

REM --- 3. quarantined states: the signature of a genuine expiry ------
echo [3] Quarantined bad states ^(invalid-state-* folders^):
powershell -NoProfile -Command ^
  "$d = Get-ChildItem -Path '%MCPDIR%' -Directory -Filter 'invalid-state-*' -ErrorAction SilentlyContinue; if (-not $d) { Write-Output '    none - no state has been judged dead' } else { Write-Output ('    {0} total, most recent:' -f $d.Count); $d | Sort-Object Name -Descending | Select-Object -First 3 | ForEach-Object { Write-Output ('      {0}' -f $_.Name) } }"
echo.

echo ============================================
echo   Verdict
echo ============================================
echo.
echo  The ONLY trustworthy auth test is a real tool call. In Claude, ask
echo  it to run get_my_profile. If your profile comes back, the login is
echo  fine no matter what any error message said.
echo.
echo  If a single server is running AND get_my_profile still fails, only
echo  then do a real login ^(close all Claude windows first^):
echo.
echo      uvx mcp-server-linkedin@latest --login
echo.
echo  Log in inside the window THAT command opens - a login in Chrome,
echo  Edge or on your phone does nothing for the robot, and can even
echo  invalidate the robot's working session.
echo.
exit /b 0
