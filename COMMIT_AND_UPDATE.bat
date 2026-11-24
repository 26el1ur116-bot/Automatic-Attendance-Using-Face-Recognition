@echo off
setlocal enabledelayedexpansion
title Git Commit & Update to GitHub
cd /d "%~dp0"

:: Locate Git executable
set "GIT_EXE=git"
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    if exist "C:\Program Files\Git\cmd\git.exe" (
        set "GIT_EXE=C:\Program Files\Git\cmd\git.exe"
    ) else (
        echo [ERROR] Git is not found! Please ensure Git for Windows is installed.
        pause
        exit /b 1
    )
)

echo ============================================================
echo          AUTOMATIC GIT COMMIT ^& UPDATE TO GITHUB            
echo ============================================================
echo.
echo Repository: https://github.com/26el1ur116-bot/Automatic-Attendance-Using-Face-Recognition
echo.

:: Show current repository status
echo [1/3] Checking for modified or new files...
"%GIT_EXE%" status --short
echo.

:: Stage all changes
"%GIT_EXE%" add -A

:: Prompt user for custom commit message
set "commit_msg="
echo ------------------------------------------------------------
set /p commit_msg="Enter your commit message (or press ENTER for default): "
echo ------------------------------------------------------------

if "%commit_msg%"=="" (
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
    set "curr_date=!datetime:~0,4!-!datetime:~4,2!-!datetime:~6,2!"
    set "curr_time=!datetime:~8,2!:!datetime:~10,2!"
    set "commit_msg=Update project changes - !curr_date! !curr_time!"
)

echo.
echo [2/3] Committing changes: "%commit_msg%"...
"%GIT_EXE%" commit -m "%commit_msg%"
echo.

echo [3/3] Uploading updates to GitHub (main branch)...
echo (If Git Credential Manager prompts in your browser, click "Authorize")
echo.
"%GIT_EXE%" push -u origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ============================================================
    echo  [SUCCESS] All changes successfully committed and updated! 
    echo ============================================================
    echo Check your repository at:
    echo https://github.com/26el1ur116-bot/Automatic-Attendance-Using-Face-Recognition
) else (
    echo ============================================================
    echo  [NOTICE] Push could not complete. Check your connection   
    echo           or browser authorization prompt.                 
    echo ============================================================
)
echo.
pause
