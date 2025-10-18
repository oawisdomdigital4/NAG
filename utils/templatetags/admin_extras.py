from django import template
from django.apps import apps
from django.contrib import admin

register = template.Library()


@register.simple_tag(takes_context=True)
def get_admin_app_list(context):
    request = context.get('request')
    if not request:
        return []
    try:
        return admin.site.get_app_list(request)
    except Exception:
        return []


@register.simple_tag
def model_count(app_label, model_name):
    try:
        Model = apps.get_model(app_label, model_name)
        return Model.objects.count()
    except Exception:
        return '—'


@register.simple_tag
def filtered_count(app_label, model_name, **filters):
    try:
        Model = apps.get_model(app_label, model_name)
        return Model.objects.filter(**filters).count()
    except Exception:
        return '—'
