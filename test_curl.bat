@echo off
REM Simple batch file to show the curl command for testing

echo ================================================================================
echo END-TO-END THUMBNAIL UPLOAD TEST
echo ================================================================================
echo.
echo Copy and paste this command into your PowerShell terminal:
echo.

echo curl -X POST ^
echo   -H "Authorization: Bearer e74a5f7e-2380-4dd5-92c9-0dd6aa8d236c" ^
echo   -H "Accept: application/json" ^
echo   -F "title=E2E Test Course" ^
echo   -F "slug=e2e-test-325c7f11" ^
echo   -F "category=Technology" ^
echo   -F "level=Beginner" ^
echo   -F "format=Self-paced" ^
echo   -F "duration=10 hours" ^
echo   -F "short_description=Test course from curl" ^
echo   -F "full_description=This is an end-to-end test of the thumbnail upload system" ^
echo   -F "price=99.99" ^
echo   -F "is_featured=false" ^
echo   -F "status=draft" ^
echo   -F "is_published=false" ^
echo   -F "thumbnail=@C:\Users\HP\NAG BACKEND\myproject\test_thumbnail.jpg" ^
echo   http://127.0.0.1:8000/api/courses/courses/

echo.
echo ================================================================================
echo AFTER RUNNING THE CURL COMMAND:
echo ================================================================================
echo.
echo 1. Check if file exists on disk:
echo    dir "C:\Users\HP\NAG BACKEND\myproject\media\course_thumbnails\"
echo.
echo 2. Verify in database with shell:
echo    python manage.py shell
echo.
echo 3. Then in the Python shell:
echo    from courses.models import Course
echo    course = Course.objects.get(slug='e2e-test-325c7f11')
echo    print("Thumbnail:", course.thumbnail)
echo    print("URL:", course.thumbnail.url if course.thumbnail else 'None')
echo.
