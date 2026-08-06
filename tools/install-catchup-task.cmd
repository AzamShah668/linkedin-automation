@echo off
REM install-catchup-task.cmd - "Job Hunt - Catch Up": run the whole pipeline, in order,
REM whenever the laptop wakes up.
REM
REM Trigger: system resume from sleep (Power-Troubleshooter event 1), delayed 2 minutes
REM so Wi-Fi is back before any LinkedIn call is attempted.
REM
REM ⚠️ Register-ScheduledTask and an -AtLogOn trigger both FAIL with "Access is denied"
REM without admin (same reason the flush task uses a timed trigger). schtasks /SC ONEVENT
REM works as a normal user, so that is what this uses. Do not "improve" this back into
REM Register-ScheduledTask unless you are running elevated.
REM
REM This does NOT replace the five scheduled tasks - it is the catch-up path for the case
REM that actually kept happening: the laptop sleeps through the day and the work never
REM runs. All runners share tools/pipeline-lock.ps1, so if a normal trigger fires at the
REM same moment, one side stands down instead of colliding.

setlocal
set TASKNAME=Job Hunt - Catch Up
set PROJ=d:\linkdin automation

schtasks /Create /TN "%TASKNAME%" ^
  /TR "powershell -NoProfile -ExecutionPolicy Bypass -File \"%PROJ%\tools\run-pipeline.ps1\"" ^
  /SC ONEVENT /EC System ^
  /MO "*[System[Provider[@Name='Microsoft-Windows-Power-Troubleshooter'] and (EventID=1)]]" ^
  /F

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo FAILED to register the task. Read the error above; do NOT assume it worked.
  exit /b 1
)

REM schtasks cannot set a trigger delay or the battery policy, so finish in PowerShell.
REM Every task in this project was silently dead on battery once - never skip this part.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$t = Get-ScheduledTask -TaskName '%TASKNAME%';" ^
  "$t.Triggers[0].Delay = 'PT2M';" ^
  "$t.Settings.StartWhenAvailable = $true;" ^
  "$t.Settings.DisallowStartIfOnBatteries = $false;" ^
  "$t.Settings.StopIfGoingOnBatteries = $false;" ^
  "$t.Settings.MultipleInstances = 'IgnoreNew';" ^
  "$t.Settings.ExecutionTimeLimit = 'PT3H';" ^
  "Set-ScheduledTask -TaskName '%TASKNAME%' -Trigger $t.Triggers -Settings $t.Settings | Out-Null;" ^
  "$v = Get-ScheduledTask -TaskName '%TASKNAME%';" ^
  "Write-Output ('delay=' + $v.Triggers[0].Delay + '  battery-blocked=' + $v.Settings.DisallowStartIfOnBatteries)"

echo.
echo Registered "%TASKNAME%" - fires 2 minutes after the machine resumes from sleep.
echo Log:    output\pipeline-log\*-pipeline.log
echo Manual: powershell -ExecutionPolicy Bypass -File "%PROJ%\tools\run-pipeline.ps1"
echo Judge it by that log, never by its exit code.
endlocal
