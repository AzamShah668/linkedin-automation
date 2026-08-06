@echo off
REM install-packet-task.cmd - register "Job Hunt - Sweep Packets" as a Windows task.
REM
REM Why: build-packet.ps1 needs a -JobId, so every discovered job used to wait for a
REM human to click Build on its row. Discovery ran daily and nothing consumed it, so
REM roles piled up unprocessed. This task drains that queue on its own.
REM
REM Timed trigger, not -AtLogOn: AtLogOn needs admin and fails with Access Denied
REM (same reason the flush task uses a timed trigger).
REM Runs every 6 hours. Each cycle builds at most 2 packets and exits in under a
REM second when the queue is empty, so idle cycles cost nothing.
REM Sends NOTHING - it only writes files and posts Slack cards to approve.

setlocal
set TASKNAME=Job Hunt - Sweep Packets
set PROJ=d:\linkdin automation

schtasks /Query /TN "%TASKNAME%" >nul 2>&1
if %ERRORLEVEL%==0 (
  echo Task already exists, replacing it.
  schtasks /Delete /TN "%TASKNAME%" /F >nul
)

schtasks /Create ^
  /TN "%TASKNAME%" ^
  /TR "powershell -NoProfile -ExecutionPolicy Bypass -File \"%PROJ%\tools\sweep-packets.ps1\" -Max 2" ^
  /SC HOURLY /MO 6 ^
  /ST 09:30 ^
  /F

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo FAILED to create the task. Read the error above; do not assume it worked.
  exit /b 1
)

echo.
echo Registered "%TASKNAME%" - every 6 hours from 09:30.
echo.
echo IMPORTANT: by default a task does not run on battery. Every scheduled task in
echo this project was silently dead for that reason once. Applying the power fix:
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s = Get-ScheduledTask -TaskName '%TASKNAME%'; $s.Settings.DisallowStartIfOnBatteries = $false; $s.Settings.StopIfGoingOnBatteries = $false; Set-ScheduledTask -TaskName '%TASKNAME%' -Settings $s.Settings | Out-Null; Write-Output ('battery settings: DisallowStartIfOnBatteries=' + (Get-ScheduledTask -TaskName '%TASKNAME%').Settings.DisallowStartIfOnBatteries)"

echo.
echo Verify with:  schtasks /Query /TN "%TASKNAME%" /V /FO LIST
echo Judge it by its LOG (output\packet-log\*-sweep.log), never by its exit code.
endlocal
