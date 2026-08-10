@echo off
REM ===================================================================
REM  LinkedIn Content Engine — Daily Dispatch Scheduled Task Installer
REM  Installs a Windows Task Scheduler job that runs at 9:00 AM IST
REM  daily to check for approved posts and dispatch them.
REM ===================================================================

set TASK_NAME=LinkedIn-ContentEngine-DailyDispatch
set PROJECT_ROOT=%~dp0..
set PYTHON=py -3
set SCRIPT=%PROJECT_ROOT%\tools\post_creator\dispatch_engine.py

echo ============================================================
echo  Installing Daily Dispatch Scheduled Task
echo  Task: %TASK_NAME%
echo  Schedule: Daily at 09:00 AM
echo  Script: %SCRIPT%
echo ============================================================

REM Delete existing task if it exists
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Create the task
REM   /sc DAILY    = run every day
REM   /st 09:00    = at 9:00 AM local time
REM   /rl HIGHEST  = run with highest privileges
REM   /np          = no password prompt (current user)
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "cmd /c \"cd /d %PROJECT_ROOT% && %PYTHON% %SCRIPT% --headless 2>>output\content_hub\dispatch.log\"" ^
    /sc DAILY ^
    /st 09:00 ^
    /rl HIGHEST ^
    /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo  [OK] Task installed successfully!
    echo  The dispatch engine will run daily at 9:00 AM.
    echo  It only posts if there is an "approved" post in the Content Hub.
    echo.
    echo  Verify with:  schtasks /query /tn "%TASK_NAME%" /v
    echo  Run now:       schtasks /run /tn "%TASK_NAME%"
    echo  Remove:        schtasks /delete /tn "%TASK_NAME%" /f
) else (
    echo.
    echo  [FAIL] Could not install task. Run as Administrator.
)
