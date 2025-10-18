Local admin theme verification

1. Activate your virtualenv if needed.

2. From project root (where manage.py lives):

```powershell
python manage.py collectstatic --noinput
python manage.py runserver
```

3. Visit http://127.0.0.1:8000/admin/ and sign in with a superuser account.

Notes
- If you don't see styles, ensure `DEBUG = True` in `myproject/settings.py` and clear the browser cache.
- The admin theme files live in:
  - `templates/admin/` (base_site.html, index.html, change_list.html)
  - `static/admin-theme/` (admin.css, admin.js)

If you'd like a Tailwind-based version or a closer pixel-match to the Ynex demo, tell me and I will regenerate the assets accordingly.
