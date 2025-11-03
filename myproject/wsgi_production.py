import os
import sys

# Add your project directory to the sys.path
path = '/home/mrokaimoses/myproject'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'

# Set environment variable to indicate we're on PythonAnywhere
os.environ['PYTHONANYWHERE_DOMAIN'] = 'newafricagroup.pythonanywhere.com'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()