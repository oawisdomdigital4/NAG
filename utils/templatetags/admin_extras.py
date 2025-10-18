from django import template
from django.apps import apps

register = template.Library()


@register.simple_tag
def model_count(app_label, model_name):
    try:
        Model = apps.get_model(app_label, model_name)
        return Model.objects.count()
    except Exception:
        return '—'
