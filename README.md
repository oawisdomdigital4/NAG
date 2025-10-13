MyProject

This repository contains a Django backend and a React + Vite frontend located under frontend/.

Quick production checklist

1. Create a Python virtualenv and install requirements

PowerShell commands:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

2. Collect static files and migrate (example with Postgres DATABASE_URL set)

PowerShell commands:
$env:DATABASE_URL = 'postgres://user:pass@host:5432/dbname'
$env:DJANGO_SECRET_KEY = 'replace-with-secret'
python manage.py migrate
python manage.py collectstatic --noinput

3. Run in production (example)

PowerShell commands:
# using gunicorn
gunicorn myproject.wsgi

Create a GitHub repo from VS Code and push

1. In VS Code Terminal (PowerShell), run:

PowerShell commands:
cd "c:\Users\HP\NAG BACKEND\myproject"
# initialize git (if not already)
git init
git add .
git commit -m "Initial import"
# create repo on GitHub (use gh cli) or create manually
# with GitHub CLI you can run:
# gh repo create your-org-or-username/your-repo --public --source=. --remote=origin --push
# Or create repo on github.com, then:
# git remote add origin https://github.com/<your>/<repo>.git
# git branch -M main
# git push -u origin main

Notes

- Replace secrets and hostnames with environment variables in production. See myproject/settings_prod.py for recommended overrides.
- If deploying to Heroku/Render, the Procfile and runtime.txt are included.
