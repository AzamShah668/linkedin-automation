@echo off
REM Start the Job Hunt dashboard and open it in the browser.
REM Double-click this file, or run it from anywhere.
cd /d "%~dp0"

py -3 backend\server.py %*
