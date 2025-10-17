Deploying this Django project to PythonAnywhere

This document shows the minimal steps to deploy the app hosted at https://github.com/oawisdomdigital4/NAG to PythonAnywhere.

Prerequisites on PythonAnywhere
- A PythonAnywhere account (free tier is fine for small sites).
- A Bash console on PythonAnywhere (or the web console) and SSH/HTTPS access to GitHub (we'll use HTTPS here).

Steps

1) Create a new web app on PythonAnywhere

- Log in to PythonAnywhere, go to the Web tab and click "Add a new web app".
- Choose Manual configuration, select Python 3.11 (or the Python version matching your runtime.txt), and create the app.

2) Open a Bash console on PythonAnywhere and clone your repo

bash commands:
git clone https://github.com/oawisdomdigital4/NAG.git
cd NAG

3) Create and activate a virtualenv

Use a virtualenv with the same Python version. Example (Python 3.11):

bash commands:
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

4) Create frontend build (optional)

If you want Django to serve the frontend static bundle, build the frontend locally and copy compiled assets into Django's `static/` location or build on PythonAnywhere (Node is not always available on free tier). Recommended: build locally and add compiled `dist` files to the repo or a separate static hosting.

5) Configure environment variables in PythonAnywhere

- In the Web tab, add environment variables under the "Environment variables" section (or export them in the virtualenvwrapper postactivate script):
  - DJANGO_SECRET_KEY
  - DATABASE_URL (if using an external DB like Heroku Postgres; PythonAnywhere supplies MySQL by default)
  - ALLOWED_HOSTS (or set to your PythonAnywhere domain in settings_prod.py)

6) Configure the WSGI file

- In the Web tab, click the WSGI configuration file link and edit it to point to your project. Example modifications (replace paths as needed):

Add near the top:
import os
import sys
project_home = '/home/yourusername/NAG'
if project_home not in sys.path:
    sys.path.insert(0, project_home)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings_prod')

Activate the virtualenv in the WSGI file by setting the path to your `.venv`.

7) Run migrations and collectstatic

bash commands (inside project and virtualenv):
python manage.py migrate --noinput
python manage.py collectstatic --noinput

8) Reload the web app

- In the Web tab, click the green Reload button.

Notes and tips
- If you use SQLite in production on PythonAnywhere, ensure the `db.sqlite3` file is within your project directory (it is by default), but SQLite is not recommended for heavy traffic.
- For external PostgreSQL use the `dj-database-url` and set `DATABASE_URL` accordingly.
- For static files, it's preferable to place production-built frontend assets on a CDN or object storage; PythonAnywhere static file mapping is available in the Web tab.

Rollback and troubleshooting
- Check the error logs (Error and Server logs in the Web tab) when the app returns 500.
- If you see import errors, ensure the virtualenv has the correct packages installed.
