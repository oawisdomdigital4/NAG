from django.utils.html import format_html


class IconAdminMixin:
    """Reusable mixin to show an icon/image preview in Django admin.

    Usage:
      - include this mixin in a ModelAdmin
      - set `icon_field = 'field_name'` on the ModelAdmin (defaults to 'logo' or 'image' or 'photo' or 'avatar')
      - add 'icon_preview' to `list_display` or `readonly_fields` as desired
    """

    icon_field = None

    def get_icon_field(self):
        if self.icon_field:
            return self.icon_field
        # sensible defaults: check declared model field names
        try:
            field_names = {f.name for f in getattr(self.model, '_meta').get_fields()}
        except Exception:
            field_names = set()
        for name in ('logo', 'image', 'photo', 'avatar'):
            if name in field_names:
                return name
        return 'logo'

    def icon_preview(self, obj):
        field_name = self.get_icon_field()
        img = None
        # prefer FileField/ImageField attribute first
        if hasattr(obj, field_name) and getattr(obj, field_name):
            media = getattr(obj, field_name)
            try:
                url = media.url
            except Exception:
                url = None
            if url:
                img = url
        # fallback to *_url attribute (like avatar_url)
        if not img:
            url_attr = f"{field_name}_url"
            if hasattr(obj, url_attr):
                val = getattr(obj, url_attr)
                if val:
                    img = val

        if not img:
            return "-"

        # small, responsive, white padded background
        html = (
            "<div style='display:flex;align-items:center;justify-content:center;" 
            "background:#fff;padding:6px;border-radius:6px;max-width:64px;max-height:64px;'>"
            f"<img src=\"{img}\" style=\"max-width:48px;max-height:48px;width:auto;height:auto;display:block;\"/>"
            "</div>"
        )
        return format_html(html)

    icon_preview.short_description = 'Icon'
    icon_preview.allow_tags = True

    class Media:
        css = {
            'all': ('admin_custom/admin.css',)
        }
