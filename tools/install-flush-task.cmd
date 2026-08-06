@echo off
REM install-flush-task.cmd — register the "flush approved sends" task (stage 1: the knock).
REM ALREADY INSTALLED on Azam's machine 2026-07-26. Kept so the setup is reproducible on a fresh machine.
REM
REM What it does: every 30 minutes it checks whether you approved any job card with a check mark in Slack.
REM If you did, it sends that person a bare LinkedIn connection request and records it so the accept-watcher
REM (install-watch-task.cmd) can deliver your CV once they accept. Nothing else is ever sent.
REM If nothing is approved it exits in under a second without waking Claude, so polling this often is cheap:
REM one small Slack read per cycle, far under Slack's rate limits.
REM Details: docs\knowledge\12-approved-send-runbook.md
REM
REM NOTE ON THE TRIGGER: a timed trigger is used rather than -AtLogOn on purpose. Registering an at-logon
REM task needs administrator rights, a timed one does not — and a timed poll is more responsive anyway,
REM since it doesn't wait for you to log out and back in.
REM MultipleInstances IgnoreNew stops a second copy starting while a real send run is still going.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -ExecutionPolicy Bypass -File \"d:\linkdin automation\tools\flush-approved.ps1\"';" ^
  "$t = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(8) -RepetitionInterval (New-TimeSpan -Minutes 30);" ^
  "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 45) -MultipleInstances IgnoreNew;" ^
  "Register-ScheduledTask -TaskName 'Job Hunt - Flush Approved' -Action $a -Trigger $t -Settings $s -Description 'Job Hunt Autopilot stage 1: every 30 min, send a bare LinkedIn connection request for anything approved with a Slack check mark.' -Force | Out-Null;" ^
  "Get-ScheduledTask -TaskName 'Job Hunt - Flush Approved' | Select-Object TaskName,State | Format-List"

echo.
echo Done. From now on: tap the check mark on a Slack job card (phone is fine, laptop can be off).
echo Within 30 minutes of the laptop being on, the connection request goes out and Slack confirms.
echo To remove it later: schtasks /Delete /TN "Job Hunt - Flush Approved" /F
pause
