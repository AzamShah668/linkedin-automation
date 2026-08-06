@echo off
REM install-watch-task.cmd — register the every-4-hours "watch for accepts" task.
REM Run by the OWNER (double-click). Claude wrote it but you install it, because it creates a task that
REM sends LinkedIn messages unattended, which is your call to authorise.
REM
REM What it does once installed: every 4 hours (while you're logged in) it checks whether anyone accepted
REM one of your pending connection requests. When someone has, it waits a random 3-20 hours (business hours
REM only, so it doesn't look like a robot) and then sends them the pitch + CV link you already approved.
REM Nothing else is ever sent. Details: docs\knowledge\13-accept-watch-runbook.md
REM
REM NOTE: this is the one job that messages people without a fresh tick from you. You approved the WORDS
REM when you reacted in Slack; this only chooses the MOMENT. To stop it at any time:
REM    schtasks /Delete /TN "Job Hunt - Watch Accepts" /F

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -ExecutionPolicy Bypass -File \"d:\linkdin automation\tools\watch-accepts.ps1\"';" ^
  "$t = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(9) -RepetitionInterval (New-TimeSpan -Hours 4);" ^
  "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 1);" ^
  "Register-ScheduledTask -TaskName 'Job Hunt - Watch Accepts' -Action $a -Trigger $t -Settings $s -Description 'Job Hunt Autopilot: every 4h, detect accepted LinkedIn invites and send the approved follow-up pitch when its delay is up.' -Force | Out-Null;" ^
  "Get-ScheduledTask -TaskName 'Job Hunt - Watch Accepts' | Select-Object TaskName,State | Format-List"

echo.
echo Done. From now on: when someone accepts your connection request, the pitch + CV goes out
echo automatically a few hours later, and Slack tells you.
echo To remove it later: schtasks /Delete /TN "Job Hunt - Watch Accepts" /F
pause
