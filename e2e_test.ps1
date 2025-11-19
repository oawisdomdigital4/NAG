# PowerShell script for end-to-end thumbnail upload test
$token = "e74a5f7e-2380-4dd5-92c9-0dd6aa8d236c"
$imagePath = "C:\Users\HP\NAG BACKEND\myproject\test_thumbnail.jpg"
$slug = "e2e-test-325c7f11"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "END-TO-END THUMBNAIL UPLOAD TEST (PowerShell Version)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

Write-Host "`n[Step 1] Verifying test image exists..." -ForegroundColor Yellow
if (Test-Path $imagePath) {
    $fileSize = (Get-Item $imagePath).Length
    Write-Host "OK Test image found: $imagePath" -ForegroundColor Green
    Write-Host "  Size: $fileSize bytes" -ForegroundColor Green
} else {
    Write-Host "ERROR Test image NOT found at $imagePath" -ForegroundColor Red
    Write-Host "  Please run: python e2e_test.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[Step 2] Preparing upload request..." -ForegroundColor Yellow
Write-Host "Token: $($token.Substring(0, 20))..." -ForegroundColor Cyan
Write-Host "Image: $imagePath" -ForegroundColor Cyan
Write-Host "Slug: $slug" -ForegroundColor Cyan

Write-Host "`n[Step 3] Sending request to backend..." -ForegroundColor Yellow

# Create multipart form data
$uri = "http://127.0.0.1:8000/api/courses/courses/"

# Read the image file as bytes
$imageBytes = [System.IO.File]::ReadAllBytes($imagePath)

# Create a new body for multipart form data
$boundary = [System.Guid]::NewGuid().ToString()
$headers = @{
    "Authorization" = "Bearer $token"
    "Accept" = "application/json"
}

# Build multipart form data
$body = @()
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="title"'
$body += ""
$body += "E2E Test Course"
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="slug"'
$body += ""
$body += $slug
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="category"'
$body += ""
$body += "Technology"
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="level"'
$body += ""
$body += "Beginner"
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="format"'
$body += ""
$body += "Self-paced"
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="duration"'
$body += ""
$body += "10 hours"
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="short_description"'
$body += ""
$body += "Test course from PowerShell curl"
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="full_description"'
$body += ""
$body += "This is an end-to-end test of the thumbnail upload system"
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="price"'
$body += ""
$body += "99.99"
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="is_featured"'
$body += ""
$body += "false"
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="status"'
$body += ""
$body += "draft"
$body += "--$boundary"
$body += 'Content-Disposition: form-data; name="is_published"'
$body += ""
$body += "false"
$body += "--$boundary"
$body += "Content-Disposition: form-data; name=`"thumbnail`"; filename=`"test_thumbnail.jpg`""
$body += "Content-Type: image/jpeg"
$body += ""

# Convert body to bytes
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes(($body -join "`r`n"))

# Append image bytes
[System.Collections.ArrayList]$fullBodyBytes = $bodyBytes
$fullBodyBytes.AddRange($imageBytes)

# Add closing boundary
$closingBoundary = "`r`n--$boundary--"
$closingBytes = [System.Text.Encoding]::UTF8.GetBytes($closingBoundary)
$fullBodyBytes.AddRange($closingBytes)

# Convert to byte array
$finalBody = [byte[]]$fullBodyBytes

# Add Content-Type header with boundary
$headers["Content-Type"] = "multipart/form-data; boundary=$boundary"

try {
    $response = Invoke-WebRequest -Uri $uri -Method POST -Headers $headers -Body $finalBody -UseBasicParsing
    
    Write-Host "`n✓ Success! Response received:" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    
    $data = $response.Content | ConvertFrom-Json
    Write-Host "`nCourse Created:" -ForegroundColor Cyan
    Write-Host "  ID: $($data.id)" -ForegroundColor Green
    Write-Host "  Title: $($data.title)" -ForegroundColor Green
    Write-Host "  Slug: $($data.slug)" -ForegroundColor Green
    Write-Host "  Thumbnail URL: $($data.thumbnail_url)" -ForegroundColor Green
    Write-Host "  Full Thumbnail: $($data.thumbnail)" -ForegroundColor Green
    
    Write-Host "`n✓ UPLOAD SUCCESSFUL!" -ForegroundColor Green
    
} catch {
    Write-Host "`n✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorBody = $reader.ReadToEnd()
        Write-Host "Error details: $errorBody" -ForegroundColor Red
    }
}

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. If successful, verify the file on disk:" -ForegroundColor Yellow
Write-Host "   dir `"C:\Users\HP\NAG BACKEND\myproject\media\course_thumbnails\`"" -ForegroundColor Cyan
Write-Host "2. Verify in database:" -ForegroundColor Yellow
Write-Host "   python manage.py shell" -ForegroundColor Cyan
Write-Host "3. Check the thumbnail URL in admin:" -ForegroundColor Yellow
Write-Host "   http://127.0.0.1:8000/admin/courses/course/" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
