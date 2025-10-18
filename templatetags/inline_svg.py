from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from pathlib import Path

register = template.Library()


@register.simple_tag
def inline_svg(filename: str, css_class: str = '') -> str:
    """Inline an SVG from static/admin/icons/bootstrap and optionally add a CSS class.

    Usage: {% inline_svg 'person.svg' 'h-4 w-4 text-current' %}
    """
    root = Path(settings.BASE_DIR) if hasattr(settings, 'BASE_DIR') else Path(__file__).resolve().parents[2]
    svg_path = root / 'static' / 'admin' / 'icons' / 'bootstrap' / filename
    try:
        content = svg_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return ''

    # Inject class into root svg tag
    if css_class:
        content = content.replace('<svg', f'<svg class="{css_class}"', 1)

    return mark_safe(content)
