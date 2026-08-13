@echo off
REM Launch Claude Code on FREE models via the local OmniRoute gateway,
REM instead of the Opus 5 subscription. Opt-in, per session - plain `claude`
REM is untouched and stays on the subscription.
REM
REM   claude-free.cmd                        auto-routing
REM   claude-free.cmd -ModelProfile glm52    a specific model profile
REM
REM Needs the gateway running (`omniroute` in another terminal).
REM See docs/knowledge/29-omniroute-gateway.md
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "tools\claude-free.ps1" %*
