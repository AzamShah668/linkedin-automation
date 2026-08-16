@echo off
REM Run the whole Job Hunt pipeline on OmniRoute free models. No Claude Code anywhere.
REM
REM   pipeline-free.cmd                 the full loop
REM   pipeline-free.cmd -Only outreach  one step
REM   pipeline-free.cmd -WhatIf         list the steps, run nothing
REM
REM This does NOT replace pipeline.cmd, which still runs the Claude stack on its schedule.
REM Both take the same pipeline lock, so they cannot collide over the one Chromium profile.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\run-pipeline-free.ps1" %*
