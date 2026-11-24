@echo off
title Push Project to GitHub
cd /d "%~dp0"
echo ============================================================
echo         PUSHING PROJECT FILES TO GITHUB REPOSITORY         
echo ============================================================
echo.
echo Repository: https://github.com/26el1ur116-bot/Automatic-Attendance-Using-Face-Recognition
echo.
echo If a browser window or Git dialog opens, click "Sign in with your browser"!
echo Since you are already logged in to Chrome, it will authenticate instantly.
echo.
"C:\Program Files\Git\cmd\git.exe" push -u origin main --force
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
