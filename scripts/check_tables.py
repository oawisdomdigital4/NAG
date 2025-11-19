import os
import sys

# Ensure we're running from project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from django.db import connection

cur = connection.cursor()
print('Applied community/payments migrations (django_migrations rows):')
cur.execute("SELECT app, name FROM django_migrations WHERE app IN ('community','payments') ORDER BY app, name")
rows = cur.fetchall()
for r in rows:
    print(r)

print('\n---- counts ----')
for t in ['community_plan','payments_plan','community_payment','payments_payment','community_subscription','payments_subscription']:
    try:
        cur.execute('SELECT COUNT(*) FROM ' + t)
        print(t, cur.fetchone()[0])
    except Exception as e:
        print(t, 'ERROR:', e)
