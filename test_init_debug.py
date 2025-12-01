#!/usr/bin/env python
"""
Debug the __init__ method to see if choices are being set properly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from summit.admin import SummitAgendaDayForm, DAY_ICON_CHOICES, DAY_COLOR_CHOICES

print("Constants:")
print("=" * 60)
print(f"DAY_ICON_CHOICES: {DAY_ICON_CHOICES}")
print(f"DAY_COLOR_CHOICES: {DAY_COLOR_CHOICES}")

print("\n\nForm instantiation:")
print("=" * 60)
form = SummitAgendaDayForm()

print("After form instantiation:")
print(f"form.fields['icon'].choices: {form.fields['icon'].choices}")
print(f"form.fields['icon'].widget.choices: {form.fields['icon'].widget.choices}")
print(f"form.fields['color'].choices: {form.fields['color'].choices}")
print(f"form.fields['color'].widget.choices: {form.fields['color'].widget.choices}")

# Check if they're the same object
print("\n\nAre field.choices and widget.choices the same?")
print("=" * 60)
print(f"Icon: {form.fields['icon'].choices is form.fields['icon'].widget.choices}")
print(f"Color: {form.fields['color'].choices is form.fields['color'].widget.choices}")

# Now try rendering
print("\n\nRendering the field:")
print("=" * 60)
bound_field = form['icon']
print(f"Bound field widget choices before render: {bound_field.field.widget.choices}")
html = str(bound_field)
print(f"HTML: {html[:100]}")
print(f"Bound field widget choices after render: {bound_field.field.widget.choices}")
