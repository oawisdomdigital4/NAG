from django.db import migrations


def create_default_plans(apps, schema_editor):
    # Prefer the canonical payments app models if they exist; fall back to community models
    try:
        Plan = apps.get_model('payments', 'Plan')
        Subscription = apps.get_model('payments', 'Subscription')
    except LookupError:
        Plan = apps.get_model('community', 'Plan')
        Subscription = apps.get_model('community', 'Subscription')
    User = None
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
    except Exception:
        User = None

    # Create plans if they do not exist
    plans = [
        {'name': 'Individual', 'price': '1.00', 'interval': 'month', 'currency': 'USD', 'role': 'individual', 'status': 'active'},
        {'name': 'Facilitator', 'price': '5.00', 'interval': 'month', 'currency': 'USD', 'role': 'facilitator', 'status': 'active'},
        {'name': 'Corporate', 'price': '500.00', 'interval': 'year', 'currency': 'USD', 'role': 'corporate', 'status': 'active'},
    ]

    created = []
    # Only set fields that exist on the historical Plan model. Payments' Plan may not have
    # 'currency', 'role' or 'status' fields, so only pass what is valid for the model.
    valid_fields = {f.name for f in Plan._meta.get_fields() if hasattr(f, 'name')}
    for p in plans:
        defaults = {}
        if 'price' in valid_fields:
            defaults['price'] = p['price']
        if 'interval' in valid_fields:
            defaults['interval'] = p['interval']
        if 'features' in valid_fields and 'features' in p:
            defaults['features'] = p.get('features', [])

        obj, _ = Plan.objects.get_or_create(name=p['name'], defaults=defaults)
        created.append(obj)

    # If a test user exists, create a subscription for them (username: test_subscriber)
    try:
        if User is not None:
            user = User.objects.filter(username='test_subscriber').first()
            if user:
                plan = Plan.objects.filter(name='Individual').first()
                if plan and not Subscription.objects.filter(user=user, plan=plan).exists():
                    import django.utils.timezone as tz
                    from datetime import timedelta
                    Subscription.objects.create(user=user, plan=plan, status='active', start_date=tz.now(), end_date=tz.now()+timedelta(days=30))
    except Exception:
        # be forgiving in migrations
        pass


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0019_add_community_features'),
    ]

    operations = [
        migrations.RunPython(create_default_plans, noop),
    ]
