@echo off
title Commit & Push to GitHub
cd /d "%~dp0"
echo ============================================================
echo         COMMIT ^& PUSH TO GITHUB REPOSITORY                
echo ============================================================
echo.
echo Repository: https://github.com/26el1ur116-bot/Automatic-Attendance-Using-Face-Recognition
echo.

:: Stage all changed and new files
"C:\Program Files\Git\cmd\git.exe" add .

:: Prompt for commit message
set "commit_msg="
set /p commit_msg="Enter commit message (or press ENTER for default): "

if "%commit_msg%"=="" (
    set commit_msg=Update project files - %date% %time%
)

echo.
echo [1/2] Committing: "%commit_msg%"...
"C:\Program Files\Git\cmd\git.exe" commit -m "%commit_msg%"

echo.
echo [2/2] Pushing to GitHub...
echo If a browser window opens, click "Sign in with your browser"!
echo.
"C:\Program Files\Git\cmd\git.exe" push -u origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ============================================================
    echo [SUCCESS] All project files successfully uploaded to GitHub!
    echo ============================================================
) else (
    echo [NOTICE] If authentication failed, please check the browser prompt.
)
echo.
pause
