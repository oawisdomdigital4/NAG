import os
import sys
import django
# ensure project root is on PYTHONPATH so 'myproject' package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

u1, created = User.objects.get_or_create(
    username='test_conn_sender', defaults={'email': 'sender@example.com'}
)
if created:
    u1.set_password('pass')
    u1.save()

u2, created = User.objects.get_or_create(
    username='test_conn_recv', defaults={'email': 'recv@example.com'}
)
if created:
    u2.set_password('pass')
    u2.save()

from django.conf import settings
# allow the test client host used by DRF's APIClient
try:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) if getattr(settings, 'ALLOWED_HOSTS', None) else []
except Exception:
    settings.ALLOWED_HOSTS = []
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

client = APIClient()
# act as sender
client.force_authenticate(user=u1)
res = client.post('/api/community/connections/', {'receiver': u2.id, 'message': 'Hello'}, format='json')
print('create', res.status_code, getattr(res, 'data', None))

res2 = client.get('/api/community/connections/')
print('list', res2.status_code, getattr(res2, 'data', None))

ress = client.get('/api/community/connections/stats/')
print('stats', ress.status_code, getattr(ress, 'data', None))

# act as receiver and accept
client.force_authenticate(user=u2)
raw = res2.data if isinstance(res2.data, list) else (res2.data.get('results') if isinstance(res2.data, dict) else None)
print('raw list data', raw)

cid = None
if raw and len(raw) > 0:
    first = raw[0]
    if isinstance(first, dict):
        cid = first.get('id')

if cid:
    res3 = client.post(f'/api/community/connections/{cid}/accept/')
    print('accept', res3.status_code, getattr(res3, 'data', None))
    ress2 = client.get('/api/community/connections/stats/')
    print('stats after accept', ress2.status_code, getattr(ress2, 'data', None))
else:
    print('No connection id found to accept')
