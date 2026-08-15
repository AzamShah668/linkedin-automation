@echo off
REM Run the whole Job Hunt pipeline once, in order.
REM
REM   pipeline.cmd                 the full loop
REM   pipeline.cmd -Only outreach  one step
REM   pipeline.cmd -WhatIf         list the steps, run nothing
REM
REM This wrapper exists because the repo path contains a space, and schtasks /TR mangles the
REM quoting of a direct `powershell -File "d:\linkdin automation\tools\run-pipeline.ps1"` call.
REM The scheduled task "Job Hunt - Full Pipeline" points here.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\run-pipeline.ps1" %*
