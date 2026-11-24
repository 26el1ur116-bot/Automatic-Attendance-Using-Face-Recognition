@echo off
title Commit & Push to GitHub
cd /d "%~dp0"
echo ============================================================
echo         GIT COMMIT ^& PUSH TO GITHUB REPOSITORY            
echo ============================================================
echo.
echo Repository: https://github.com/26el1ur116-bot/Automatic-Attendance-Using-Face-Recognition
echo.

:: Stage all current files and changes
"C:\Program Files\Git\cmd\git.exe" add .

:: Prompt user for custom commit message
set "commit_msg="
set /p commit_msg="Enter your commit message (or press ENTER for default): "

if "%commit_msg%"=="" (
    set commit_msg=Update project files - %date% %time%
)

echo.
echo [1/2] Committing changes with message: "%commit_msg%"...
"C:\Program Files\Git\cmd\git.exe" commit -m "%commit_msg%"

echo.
echo [2/2] Pushing commits to GitHub (main branch)...
echo If a browser window opens, click "Sign in with your browser" / "Authorize".
echo.
"C:\Program Files\Git\cmd\git.exe" push -u origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ============================================================
    echo [SUCCESS] Committed and pushed all changes to GitHub!
    echo ============================================================
) else (
    echo [NOTICE] If push did not complete, verify your network or browser authorization.
)
echo.
pause
