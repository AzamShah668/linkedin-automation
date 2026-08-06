@echo off
REM publish-cv.cmd — one-time publish of the tailored CV PDFs to a public GitHub repo.
REM Run by the OWNER (double-click or run in a terminal). Claude wrote it but you execute it,
REM because publishing your personal CV to the public internet is your call.
REM After it succeeds, tell Claude "published" and the links go into your Gmail drafts.

setlocal
set PROJ=d:\linkdin automation
set WORK=%TEMP%\cv-publish
set REPO=cv

echo === Job Hunt Autopilot: publish CVs to github.com/AzamShah668/%REPO% ===

rmdir /s /q "%WORK%" 2>nul
mkdir "%WORK%"
cd /d "%WORK%"

REM 1. Create the public repo (ok if it already exists)
gh repo create AzamShah668/%REPO% --public --description "Azam Rizwan Shah - CV (tailored variants)" 2>nul

REM 2. Clone it
gh repo clone AzamShah668/%REPO% repo || git clone https://github.com/AzamShah668/%REPO%.git repo
cd repo

REM 3. Copy CVs with ROLE-based names (never company names - recruiters must not see other applications)
copy /y "%PROJ%\output\pdf\2-Infosys-AI-Application-Engineer.pdf"          "Azam-Shah-CV-AI-Engineer.pdf" >nul
copy /y "%PROJ%\output\pdf\1-Innova-ESI-DevOps-Engineer.pdf"               "Azam-Shah-CV-DevOps-Engineer.pdf" >nul
copy /y "%PROJ%\output\pdf\3-GoodSpace-Forward-Deployed-Engineer.pdf"      "Azam-Shah-CV-Forward-Deployed-Engineer.pdf" >nul

REM 4. Commit + push
git add -A
git commit -m "Add tailored CV variants (AI, DevOps, FDE)"
git branch -M main
git push -u origin main

echo.
echo === DONE. Links: ===
echo https://github.com/AzamShah668/cv/blob/main/Azam-Shah-CV-AI-Engineer.pdf
echo https://github.com/AzamShah668/cv/blob/main/Azam-Shah-CV-DevOps-Engineer.pdf
echo https://github.com/AzamShah668/cv/blob/main/Azam-Shah-CV-Forward-Deployed-Engineer.pdf
echo.
echo Now tell Claude: "published" - and the links go into your Gmail drafts.
pause
