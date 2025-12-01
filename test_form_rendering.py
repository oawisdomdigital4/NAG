#!/usr/bin/env python
"""
Detailed test of form field rendering to see what's happening
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from summit.admin import SummitAgendaDayForm
from django.forms.widgets import RadioSelect

# Instantiate form
form = SummitAgendaDayForm()

# Get the icon field widget
icon_field = form.fields['icon']
icon_widget = icon_field.widget

print("Icon Field Analysis")
print("=" * 60)
print(f"Widget type: {type(icon_widget).__name__}")
print(f"Is RadioSelect: {isinstance(icon_widget, RadioSelect)}")
print(f"Choices: {len(icon_widget.choices)} items")

# Manually render the widget
print("\nManual widget render:")
print("-" * 60)
try:
    # Try rendering with attrs
    html = icon_widget.render('icon', icon_field.initial, attrs={'id': 'id_icon'})
    print(f"HTML length: {len(html)}")
    print(f"HTML content:\n{html}")
except Exception as e:
    print(f"Error: {e}")

# Also check the form's actual field rendering
print("\n\nForm field rendering via BoundField:")
print("=" * 60)
bound_field = form['icon']
print(f"BoundField widget: {type(bound_field.field.widget).__name__}")
print(f"BoundField HTML:")
print(bound_field)

# Check what template the widget is using
print("\n\nWidget template information:")
print("=" * 60)
print(f"Widget template_name: {getattr(icon_widget, 'template_name', 'NOT SET')}")
print(f"Widget default attrs: {getattr(icon_widget, 'attrs', {})}")

# Check if it's an admin widget
from django.contrib.admin.widgets import AdminRadioSelect
print(f"Is AdminRadioSelect: {isinstance(icon_widget, AdminRadioSelect)}")
