#!/bin/bash
echo "🚀 Pulling latest code from GitHub..."
git pull origin main

echo "📦 Activating virtual environment..."
source /home/newafricagroup/.venv/bin/activate

echo "🛠️  Applying migrations..."
python manage.py migrate

echo "🧹 Collecting static files..."
python manage.py collectstatic --noinput

echo "🔄 Reloading web app..."
/home/newafricagroup/.venv/bin/pa_reload_webapp newafricagroup.pythonanywhere.com

echo "✅ Deployment complete!"
