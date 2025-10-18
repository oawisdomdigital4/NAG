#!/bin/bash

# Navigate to your project folder
cd ~/NAG || exit

echo "🚀 Starting deployment to PythonAnywhere..."

# Pull latest code from GitHub
echo "📦 Pulling latest code from GitHub..."
git pull origin main

# Activate your virtual environment
echo "🧠 Activating virtual environment..."
source .venv/bin/activate

# Apply database migrations
echo "🗃️ Applying migrations..."
python manage.py migrate --noinput

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# Reload the web app on PythonAnywhere
echo "🔄 Reloading web app..."
pa_reload_webapp newafricagroup.pythonanywhere.com

echo "✅ Deployment complete!"
