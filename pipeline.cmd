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
REM Suppresses the brain1-patterns SessionStart hook for the headless Claude sessions this spawns.
REM Measured 2026-08-17: across 96 archived scheduled-runner transcripts those sessions read the
REM Obsidian vault ZERO times - they follow a runbook and exit - so injecting its index costs
REM ~1,400 tokens per run for nothing. A human session never has this set. See
REM docs/knowledge/35-knowledge-system-audit.md section 7.
set CLAUDE_UNATTENDED=1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\run-pipeline.ps1" %*
