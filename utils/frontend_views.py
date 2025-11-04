from pathlib import Path
from django.http import FileResponse, HttpResponseNotFound
from django.conf import settings


def serve_spa(request, path=''):
    """Serve the SPA index.html for client-side routes.

    This will attempt to find a built frontend at one of several
    likely locations and return its index.html. It intentionally
    excludes API, admin, static and media paths at the URLconf level.
    """
    base = Path(settings.BASE_DIR)
    candidates = [
        base / 'frontend' / 'dist' / 'index.html',
        base / 'frontend' / 'build' / 'index.html',
        base / 'frontend' / 'index.html',
        base / 'static' / 'index.html',
        base / 'templates' / 'index.html',
    ]

    for p in candidates:
        try:
            if p.exists():
                return FileResponse(open(p, 'rb'), content_type='text/html')
        except Exception:
            # If reading fails for any reason, try the next candidate
            continue

    return HttpResponseNotFound('index.html not found')
