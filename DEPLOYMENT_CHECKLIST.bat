@echo off
REM Deployment helper script for Breezehost
REM This shows you what files need to be uploaded

echo ============================================
echo   PRODUCTION DEPLOYMENT CHECKLIST
echo   Course Module Creation Fix - Dec 1, 2025
echo ============================================
echo.
echo CURRENT STATUS:
echo - Frontend build: READY ✓
echo - Fix applied: content field now sends '{}' string instead of array ✓
echo - Files to upload: 12 files in dist/ folder
echo.
echo ============================================
echo   FILES TO UPLOAD
echo ============================================
echo.
echo CRITICAL (Must Upload):
echo   1. dist\index.html (474 bytes)
echo   2. dist\assets\index-ByJNxS-U.css (116 KB)
echo   3. dist\assets\index-P2RY9ksP.js (438 KB) - FIXED COURSE CREATION
echo   4. dist\assets\index-DRrBaE32.js (2.8 MB)
echo   5. dist\assets\pdf-BAFhSO9X.js (446 KB)
echo.
echo OPTIONAL (Nice to Have):
echo   - dist\nag_cert.pdf
echo   - dist\page-flip.mp3
echo   - dist\pdf.worker.min.js
echo   - dist\TNAG Black Logo.png
echo   - dist\notifications\ folder
echo   - dist\engagement\ folder
echo.
echo ============================================
echo   DEPLOYMENT INSTRUCTIONS
echo ============================================
echo.
echo 1. Access Breezehost cPanel:
echo    https://thenewafricagroup.com:2083/
echo    OR: Breezehost Dashboard ^> cPanel
echo.
echo 2. Open File Manager ^> Navigate to: /home/USERNAME/public_html/
echo.
echo 3. Delete old files:
echo    - Select index.html, click Delete
echo    - Select assets folder, click Delete
echo.
echo 4. Upload new files:
echo    - Upload index.html from: %CD%\dist\
echo    - Upload assets/ folder from: %CD%\dist\
echo.
echo 5. Hard refresh browser:
echo    Windows: Ctrl+F5
echo    Mac: Cmd+Shift+R
echo.
echo 6. Test course creation:
echo    - Open DevTools (F12)
echo    - Go to Console tab
echo    - Try creating a course
echo    - Look for: "Creating module with payload: ... content: '{}'"
echo.
echo ============================================
echo   WHAT WAS FIXED
echo ============================================
echo.
echo File: frontend/src/hooks/useCourseCreation.ts (Line 161)
echo.
echo BEFORE:
echo   content: module.lessons || [],  // Sent ARRAY - BROKEN!
echo.
echo AFTER:
echo   content: '{}',  // Sends JSON STRING - FIXED!
echo.
echo Why: Backend CourseModuleSerializer expects CharField,
echo       not an array. Now frontend sends proper JSON string.
echo.
echo ============================================
echo   READY FOR DEPLOYMENT
echo ============================================
echo.
echo Next steps:
echo 1. Go to Breezehost cPanel
echo 2. Upload files from:
echo    %CD%\dist\
echo 3. Verify in browser
echo.
echo For detailed guide, see:
echo   PRODUCTION_DEPLOYMENT_GUIDE.md
echo.
pause
