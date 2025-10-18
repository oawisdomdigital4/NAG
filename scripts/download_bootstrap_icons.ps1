# Downloads selected Bootstrap Icons SVGs to static/admin/icons/bootstrap and patches them to use fill="currentColor"
# Usage: Open PowerShell in the repo root and run: .\scripts\download_bootstrap_icons.ps1

$icons = @(
  'clock-history',
  'people',
  'person',
  'people-fill',
  'person-badge',
  'person-circle',
  'journal-bookmark',
  'journal-richtext',
  'credit-card',
  'cash-stack',
  'bell',
  'globe'
)

$destDir = "static/admin/icons/bootstrap"
if (-not (Test-Path $destDir)) {
  New-Item -ItemType Directory -Path $destDir -Force | Out-Null
}

foreach ($icon in $icons) {
  $url = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/$icon.svg"
  $out = Join-Path $destDir "$icon.svg"
  Write-Host "Downloading $icon..."
  try {
    Invoke-RestMethod -Uri $url -OutFile $out -UseBasicParsing -ErrorAction Stop
    # Patch the SVG to use fill="currentColor" on the root <svg> tag if not already present
    $svg = Get-Content $out -Raw
    if ($svg -notmatch 'fill="currentColor"') {
      $svg = $svg -replace '<svg([^>]*)>', '<svg$1 fill="currentColor">'
      Set-Content -Path $out -Value $svg -Encoding UTF8
    }
    Write-Host "Saved $out"
  } catch {
    # Avoid interpolation issues inside double-quoted strings by using -f formatting
    Write-Warning ("Failed to download {0}: {1}" -f $icon, $_)
  }
}

Write-Host "Done. Remember to run 'python manage.py collectstatic' if running in production."