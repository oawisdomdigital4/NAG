#!/usr/bin/env python
"""
Quick test to verify SummitAgendaDayForm renders icon and color as RadioSelect widgets.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from summit.admin import SummitAgendaDayForm
from summit.models import SummitAgendaDay

# Test 1: Instantiate form without instance (new record)
print("=" * 60)
print("TEST 1: Form for new SummitAgendaDay (no instance)")
print("=" * 60)
form = SummitAgendaDayForm()

print(f"\n✓ Form instantiated successfully")
print(f"✓ Form fields: {list(form.fields.keys())}")

# Check icon field
icon_field = form.fields.get('icon')
if icon_field:
    print(f"\n✓ Icon field widget: {type(icon_field.widget).__name__}")
    print(f"  Widget class: {icon_field.widget.__class__}")
    print(f"  Initial value: {icon_field.initial}")
    print(f"  Choices count: {len(icon_field.choices)}")
    if icon_field.choices:
        print("  Sample choices:")
        for i, (val, label) in enumerate(icon_field.choices[:3]):
            print(f"    [{i}] Value: {repr(val)}, Label: {label}")
else:
    print("\n✗ Icon field NOT found!")

# Check color field
color_field = form.fields.get('color')
if color_field:
    print(f"\n✓ Color field widget: {type(color_field.widget).__name__}")
    print(f"  Widget class: {color_field.widget.__class__}")
    print(f"  Initial value: {color_field.initial}")
    print(f"  Choices count: {len(color_field.choices)}")
    if color_field.choices:
        print("  Sample choices:")
        for i, (val, label) in enumerate(color_field.choices[:3]):
            print(f"    [{i}] Value: {repr(val)}, Label type: {type(label).__name__}, Label: {label}")
else:
    print("\n✗ Color field NOT found!")

# Test 2: Try to render the form as HTML
print("\n" + "=" * 60)
print("TEST 2: Form HTML rendering")
print("=" * 60)
try:
    form_html = str(form)
    print(f"✓ Form renders to HTML successfully")
    print(f"  HTML length: {len(form_html)} characters")
    
    # Check for RadioSelect in the output
    if 'radio' in form_html.lower():
        print(f"  ✓ Found 'radio' in HTML (RadioSelect is being used)")
    else:
        print(f"  ✗ 'radio' not found in HTML (might be using different widget)")
        
except Exception as e:
    print(f"✗ Error rendering form: {e}")

# Test 3: Check the actual form HTML for icon and color fields
print("\n" + "=" * 60)
print("TEST 3: Field-specific HTML")
print("=" * 60)
try:
    icon_html = str(form['icon'])
    print(f"✓ Icon field renders: {len(icon_html)} characters")
    if 'type="radio"' in icon_html:
        print(f"  ✓ Icon field has radio buttons")
    else:
        print(f"  ✗ Icon field does NOT have radio buttons")
    print(f"  Preview: {icon_html[:200]}...")
    
except Exception as e:
    print(f"✗ Error rendering icon field: {e}")

try:
    color_html = str(form['color'])
    print(f"\n✓ Color field renders: {len(color_html)} characters")
    if 'type="radio"' in color_html:
        print(f"  ✓ Color field has radio buttons")
    else:
        print(f"  ✗ Color field does NOT have radio buttons")
    print(f"  Preview: {color_html[:200]}...")
    
except Exception as e:
    print(f"✗ Error rendering color field: {e}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
