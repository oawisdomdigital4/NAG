import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from utils.models import TeamMember
from utils.serializers import TeamMemberSerializer

qs = TeamMember.objects.all()
result = []
for m in qs:
    try:
        ser = TeamMemberSerializer(m, context={'request': None})
        result.append(ser.data)
    except Exception as e:
        print('ERROR serializing', m.id, str(e))
        raise

print(json.dumps(result, indent=2, default=str))
