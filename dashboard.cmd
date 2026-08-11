@echo off
REM Start the Job Hunt dashboard and open it in the browser.
REM Double-click this file, or run it from anywhere.
cd /d "%~dp0"

echo Refreshing the Slack mirror...
py -3 tools\slack_export.py
if errorlevel 1 echo   (Slack refresh skipped - showing the last export)

echo.
py -3 backend\server.py %*
