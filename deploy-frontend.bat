@echo off
REM Deploy frontend to Breezehost via SFTP
REM Make sure you have WinSCP or PuTTY installed

echo.
echo ========================================
echo Frontend Deployment to Breezehost
echo ========================================
echo.

REM Check if dist folder exists
if not exist "frontend\dist" (
    echo [ERROR] frontend\dist folder not found
    echo Run "npm run build" in the frontend folder first
    exit /b 1
)

echo [OK] dist folder found
echo.

REM Configuration - MODIFY THESE VALUES
set REMOTE_HOST=thenewafricagroup.com
set REMOTE_USER=your_breezehost_username
set REMOTE_PATH=/home/your_username/public_html
set BREEZEHOST_PASSWORD=your_password_here

echo Configuration:
echo   Host: %REMOTE_HOST%
echo   User: %REMOTE_USER%
echo   Remote Path: %REMOTE_PATH%
echo.

REM Create SFTP batch file for WinSCP
echo Creating SFTP script...
(
    echo open sftp://%REMOTE_USER%:%BREEZEHOST_PASSWORD%@%REMOTE_HOST%/
    echo cd %REMOTE_PATH%
    echo lcd frontend\dist
    echo put -r *
    echo close
    echo exit
) > temp-sftp-script.txt

REM Try using WinSCP command line
echo.
echo Uploading files...
winscp.com /script=temp-sftp-script.txt

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Deployment complete!
    echo Frontend deployed to: https://%REMOTE_HOST%
    echo.
    echo Next steps:
    echo 1. Clear your browser cache (Ctrl+Shift+Del)
    echo 2. Test the group update feature
    echo 3. Verify group updates now work
    del temp-sftp-script.txt
) else (
    echo.
    echo [ERROR] Deployment failed
    echo Make sure WinSCP is installed and in PATH
    pause
    exit /b 1
)
