from django.contrib import admin
from django.utils.html import format_html
from django import forms
import datetime
import json
from django.utils.safestring import mark_safe
from .models import(
    SummitAgendaDay, 
    SummitAgendaItem,
    Organizer,
    FeaturedSpeaker,
    Partner,
    PartnerSection,
    PastEdition,
    SummitHero,
    SummitStat,
    SummitAbout,
    SummitPillar,
    SummitKeyThemes,
    SummitTheme,
    SummitAgenda,
    SummitAgendaDay,
    RegistrationPackage,
    SummitAgendaItem,
	ICON_CHOICES,
)

# Color choices used for registration packages when SummitTheme is not available
PACKAGE_COLOR_CHOICES = [
    ('', 'Default'),
    ('from-blue-500 to-brand-blue', 'Blue gradient'),
    ('from-brand-gold to-yellow-600', 'Gold gradient'),
    ('from-purple-500 to-pink-500', 'Purple gradient'),
    ('from-green-500 to-emerald-500', 'Green gradient'),
    ('from-indigo-500 to-blue-500', 'Indigo gradient'),
]

DAY_COLOR_CHOICES = [
	('', 'Default'),
	('from-blue-500 to-brand-blue', 'Blue gradient'),
	('from-brand-gold to-yellow-600', 'Gold gradient'),
	('from-purple-500 to-pink-500', 'Purple gradient'),
	('from-green-500 to-emerald-500', 'Green gradient'),
	('from-indigo-500 to-blue-500', 'Indigo gradient'),
]


# Helpful choices for SummitAgendaDay visuals
DAY_ICON_CHOICES = [
	('', '— None —'),
	('🎤', 'Microphone 🎤'),
	('👥', 'People 👥'),
	('🏆', 'Award 🏆'),
	('🌍', 'Globe 🌍'),
	('⭐', 'Star ⭐'),
]



# sensible defaults used to prefill new forms
DEFAULT_DAY_ICON = '🎤'
DEFAULT_DAY_COLOR = 'from-blue-500 to-brand-blue'

# module-level mapping for pillar icons (used by inline and form)
PILLAR_ICON_EMOJI = {
	'Target': '🎯',
	'Compass': '🧭',
	'Lightbulb': '💡',
	'Users': '👥',
	'Globe': '🌍',
}

# Theme icon emoji mapping for admin preview
THEME_ICON_EMOJI = {
    'Bot': '🤖',
    'GraduationCap': '🎓',
    'Handshake': '🤝',
    'Sprout': '🌱',
    'TrendingUp': '📈',
}

class RegistrationPackageForm(forms.ModelForm):
	class Meta:
		model = RegistrationPackage
		fields = '__all__'
		widgets = {
			'color': forms.RadioSelect,
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# No icon choices; icons removed for registration packages

		# Build color choices with a small preview similar to SummitTheme
		if 'color' in self.fields:
			try:
				try:
					from .models import SummitTheme
					palette = getattr(SummitTheme, 'COLOR_CHOICES_THEME', PACKAGE_COLOR_CHOICES)
				except Exception:
					palette = PACKAGE_COLOR_CHOICES

				color_choices = []
				for val, lab in palette:
					if not val:
						color_choices.append((val, lab))
						continue
					preview = f"<div class='{val.replace('from-', 'bg-').replace('to-', '')}' style='display:inline-block;width:20px;height:20px;border-radius:4px;margin-right:8px;vertical-align:middle'></div>"
					display = mark_safe(f"{preview} {lab}")
					color_choices.append((val, display))
				self.fields['color'].choices = color_choices
			except Exception:
				pass



@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
	list_display = ("icon", "name")
	# Restrict the admin create/edit form to only the prototype fields
	# so admins only supply name, bio and image.
	fields = ("name", "bio", "image")

	def icon(self, obj):
		# small organizer icon; prefer a logo/avatar field if present
		img = getattr(obj, 'logo', None) or getattr(obj, 'avatar', None)
		if img:
			try:
				url = img.url if hasattr(img, 'url') else img
				return format_html("<img src='{}' style='max-height:36px; border-radius:6px' />", url)
			except Exception:
				pass
		return format_html("<i class='fas fa-user-tie' style='font-size:16px;color:#0D1B52;'></i>")
	icon.short_description = ''


@admin.register(FeaturedSpeaker)
class FeaturedSpeakerAdmin(admin.ModelAdmin):
	list_display = ("icon", "name", "location")
	# Admin form limited to prototype fields: name, bio, location and image
	fields = ("name", "bio", "location", "image")

	def icon(self, obj):
		img = getattr(obj, 'photo', None) or getattr(obj, 'avatar', None) or getattr(obj, 'image', None)
		if img:
			try:
				url = img.url if hasattr(img, 'url') else img
				return format_html("<img src='{}' style='max-height:36px; border-radius:6px' />", url)
			except Exception:
				pass
		return format_html("<i class='fas fa-microphone' style='font-size:16px;color:#0D1B52;'></i>")
	icon.short_description = ''


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
	list_display = ("icon", "id", "logo_preview")

	def icon(self, obj):
		return format_html("<i class='fas fa-building' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''

	def logo_preview(self, obj):
		# If partner has an uploaded logo show thumbnail, otherwise show a Font Awesome icon
		if getattr(obj, 'logo', None):
			try:
				return format_html("<img src='{}' style='max-height:48px; object-fit:contain;'/>", obj.logo.url)
			except Exception:
				pass
		return format_html("<i class='fas fa-handshake' style='font-size:22px;color:#0D1B52;'></i>")
	logo_preview.short_description = "Logo"


@admin.register(RegistrationPackage)
class RegistrationPackageAdmin(admin.ModelAdmin):
	"""Admin for registration packages used by the public registration page."""
	# show description and a small color preview in the list for quicker scanning
	list_display = ('icon', 'id', 'name', 'description', 'color_preview', 'price', 'currency', 'popular', 'order')
	list_filter = ('popular',)
	search_fields = ('name',)
	# expose description so editors can edit the card subtitle shown in the frontend
	# Keep editable fields simple; put non-editable previews and timestamps in readonly_fields
	fields = (
		'name', 'description', 'price', 'currency', 'features', 'popular', 'order',
		'color_preview', 'color'
	)

	readonly_fields = ('color_preview', 'created_at')

	form = RegistrationPackageForm

	def icon(self, obj):
		return format_html("<i class='fas fa-ticket-alt' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''

	def icon_preview(self, obj):
		try:
			# icons removed for RegistrationPackage
			return ''
		except Exception:
			return ''


	def color_preview(self, obj):
		try:
			if obj and getattr(obj, 'color', None):
				# Try to render a small gradient preview. Convert gradient classes
				# to inline style fallback when applicable for admin preview.
				cls = obj.color
				# convert to a simple background color string for preview if possible
				preview_style = ''
				if 'gray' in cls:
					preview_style = 'background:linear-gradient(90deg,#4b5563,#374151)'
				elif 'gold' in cls or 'amber' in cls:
					preview_style = 'background:linear-gradient(90deg,#f6e05e,#f59e0b)'
				elif 'red' in cls:
					preview_style = 'background:linear-gradient(90deg,#ef4444,#b91c1c)'
				elif 'blue' in cls:
					preview_style = 'background:linear-gradient(90deg,#3b82f6,#2563eb)'
				else:
					preview_style = ''
				return format_html(
					"<div style='width:60px;height:24px;border-radius:6px;{}'></div>",
					preview_style
				)
			return ''
		except Exception:
			return ''
	color_preview.short_description = 'Color Preview'

	def formfield_for_dbfield(self, db_field, request, **kwargs):
		"""Prefer RadioSelect for icon and color fields so choices render as radios."""
		try:
			if db_field.name == 'color':
				return db_field.formfield(widget=forms.RadioSelect, choices=PACKAGE_COLOR_CHOICES)
		except Exception:
			pass
		return super().formfield_for_dbfield(db_field, request, **kwargs)

	class Media:
		css = {
			'all': ('admin/css/custom-theme.css',)
		}
		js = (
			'admin/js/registration_package_select.js',
		)


@admin.register(PastEdition)
class PastEditionAdmin(admin.ModelAdmin):
	list_display = ("icon", "year", "location", "theme")
	readonly_fields = ()

	def icon(self, obj):
		return format_html("<i class='fas fa-history' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''



@admin.register(SummitHero)
class SummitHeroAdmin(admin.ModelAdmin):
	list_display = ('icon', 'id', 'title_main', 'title_highlight', 'is_published', 'created_at')
	readonly_fields = ('created_at',)
	
	def icon(self, obj):
		return format_html("<i class='fas fa-image' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''

	def icon(self, obj):
		return format_html("<i class='fas fa-image' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''
	fields = (
		'title_main', 'title_highlight', 'date_text', 'location_text',
		'subtitle', 'strapline', 'background_image',
		'cta_register_label', 'cta_register_url', 'cta_brochure_label', 'cta_brochure_url', 'is_published', 'created_at'
	)
	# use inline editing for stats (dropdown for icon, text for label/value)
	class SummitStatInline(admin.TabularInline):
		model = SummitStat
		extra = 1
		# show a small icon preview (emoji) next to the dropdown
		fields = ('icon_preview', 'icon', 'label', 'value', 'order')
		readonly_fields = ('icon_preview',)

		def icon_preview(self, obj):
			try:
				return format_html("<span style='font-size:20px;line-height:1'>{}</span>", obj.icon or '')
			except Exception:
				return ''

		icon_preview.short_description = 'Icon'
        
		# Use radio buttons with emoji labels in the inline form
		class SummitStatForm(forms.ModelForm):
			class Meta:
				model = SummitStat
				fields = '__all__'
				widgets = {
					'icon': forms.RadioSelect,
				}

			def __init__(self, *args, **kwargs):
				super().__init__(*args, **kwargs)
				# build choices with visible emoji + label
				choices = []
				for val, lab in ICON_CHOICES:
					display = f"{val} {lab}"
					choices.append((val, mark_safe(display)))
				self.fields['icon'].choices = choices

		form = SummitStatForm

	inlines = [SummitStatInline]


@admin.register(PartnerSection)
class PartnerSectionAdmin(admin.ModelAdmin):
	"""Simple admin for editing partners CTA/section content."""
	list_display = ('icon', 'id', 'partner_section_title', 'is_published', 'created_at')
	readonly_fields = ('created_at', 'updated_at')
	
	def icon(self, obj):
		return format_html("<i class='fas fa-users' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''

	def icon(self, obj):
		return format_html("<i class='fas fa-link' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''
	fields = (
		'partner_section_title', 'partner_section_subtitle',
		'partner_cta_label', 'partner_cta_url', 'is_published', 'created_at'
	)
	

@admin.register(SummitAbout)
class SummitAboutAdmin(admin.ModelAdmin):
	list_display = ('icon', 'id', 'title_main', 'title_highlight', 'created_at')
	readonly_fields = ('created_at',)
	
	def icon(self, obj):
		return format_html("<i class='fas fa-info-circle' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''

	def icon(self, obj):
		return format_html("<i class='fas fa-info-circle' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''

	class SummitPillarInline(admin.TabularInline):
		model = SummitPillar
		extra = 1
		# show a preview emoji for each pillar icon choice
		fields = ('icon_preview', 'icon', 'title', 'description', 'order')
		readonly_fields = ('icon_preview',)

		ICON_EMOJI = PILLAR_ICON_EMOJI

		def icon_preview(self, obj):
			try:
				emoji = PILLAR_ICON_EMOJI.get(getattr(obj, 'icon', ''), '')
				return format_html("<span style='font-size:20px;line-height:1'>{}</span>", emoji)
			except Exception:
				return ''

		icon_preview.short_description = 'Icon'
        
		class SummitPillarForm(forms.ModelForm):
			class Meta:
				model = SummitPillar
				fields = '__all__'
				widgets = {
					'icon': forms.RadioSelect,
				}

			def __init__(self, *args, **kwargs):
				super().__init__(*args, **kwargs)
				choices = []
				for val, lab in SummitPillar.ICON_CHOICES_PILLAR:
					emoji = PILLAR_ICON_EMOJI.get(val, '')
					display = f"{emoji} {lab}"
					choices.append((val, mark_safe(display)))
				self.fields['icon'].choices = choices

		form = SummitPillarForm

	inlines = [SummitPillarInline]


@admin.register(SummitKeyThemes)
class SummitKeyThemesAdmin(admin.ModelAdmin):
	# show the two-part title in the list so editors can see/adjust the highlighted
	# portion from the admin rather than relying on a hard-coded frontend string
	list_display = ('icon', 'id', 'title_main', 'title_highlight', 'created_at')
	readonly_fields = ('created_at',)
	
	def icon(self, obj):
		return format_html("<i class='fas fa-lightbulb' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''

	def icon(self, obj):
		return format_html("<i class='fas fa-star' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''

	# Allow admins to edit the section-level CTA text and URL from the same form
	fields = ('title_main', 'title_highlight', 'subtitle', 'cta_label', 'cta_url', 'created_at')

	class SummitThemeInline(admin.TabularInline):
		model = SummitTheme
		extra = 1
		fields = ('icon_preview', 'icon', 'color_preview', 'color', 'title', 'subtitle', 'description', 'order')
		readonly_fields = ('icon_preview', 'color_preview')

		def icon_preview(self, obj):
			try:
				emoji = THEME_ICON_EMOJI.get(getattr(obj, 'icon', ''), '')
				return format_html("<span style='font-size:20px;line-height:1'>{}</span>", emoji)
			except Exception:
				return ''
		icon_preview.short_description = 'Icon'

		def color_preview(self, obj):
			try:
				# Show an actual color preview with the gradient
				if obj and obj.color:
					gradient = obj.color.replace('from-', 'bg-').replace('to-', '')
					return format_html(
						"<div class='{}' style='width:40px; height:20px; border-radius:4px'></div>",
						gradient
					)
				return ''
			except Exception:
				return ''
		color_preview.short_description = 'Preview'

		class SummitThemeForm(forms.ModelForm):
			class Meta:
				model = SummitTheme
				fields = '__all__'
				widgets = {
					'icon': forms.RadioSelect,
					'color': forms.RadioSelect,
				}

			def __init__(self, *args, **kwargs):
				super().__init__(*args, **kwargs)
				# Icon choices with emoji
				choices = []
				for val, lab in SummitTheme.ICON_CHOICES_THEME:
					emoji = THEME_ICON_EMOJI.get(val, '')
					display = f"{emoji} {lab}"
					choices.append((val, mark_safe(display)))
				self.fields['icon'].choices = choices

				# Color choices with preview
				color_choices = []
				for val, lab in SummitTheme.COLOR_CHOICES_THEME:
					# Create a preview div with the actual gradient
					preview = f"<div class='{val.replace('from-', 'bg-').replace('to-', '')}' style='display:inline-block;width:20px;height:20px;border-radius:4px;margin-right:8px;vertical-align:middle'></div>"
					display = f"{preview} {lab}"
					color_choices.append((val, mark_safe(display)))
				self.fields['color'].choices = color_choices

		form = SummitThemeForm

	inlines = [SummitThemeInline]


@admin.register(SummitAgenda)
class SummitAgendaAdmin(admin.ModelAdmin):
	# Updated to match current SummitAgenda model
	list_display = ('icon', 'id', 'title', 'created_at')
	# created_at and updated_at are non-editable auto timestamps; show as readonly
	readonly_fields = ('created_at', 'updated_at')
	
	def icon(self, obj):
		return format_html("<i class='fas fa-calendar' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''

	def icon(self, obj):
		return format_html("<i class='fas fa-calendar' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''
	fields = ('title', 'description', 'created_at')

	def get_changeform_initial_data(self, request):
		"""Prefill the create/change form with sensible defaults or the latest agenda values."""
		try:
			latest = SummitAgenda.objects.order_by('-created_at').first()
			if latest:
				return {'title': latest.title or '', 'description': latest.description or ''}
		except Exception:
			pass
		return {'title': 'Summit', 'description': 'Two transformative days of dialogue, partnership, and recognition'}

	class SummitAgendaDayInline(admin.TabularInline):
		model = SummitAgendaDay
		extra = 1
		# Use fields that exist on the current SummitAgendaDay model
		fields = ('title', 'date', 'location', 'activities_table', 'order')
		readonly_fields = ()
		exclude = ()

		class SummitAgendaDayForm(forms.ModelForm):
			activities_table = forms.CharField(widget=forms.HiddenInput(), required=False)

			class Meta:
				model = SummitAgendaDay
				fields = '__all__'

			def __init__(self, *args, **kwargs):
				super().__init__(*args, **kwargs)
				initial = getattr(self.instance, "activities", [])
				try:
					self.fields["activities_table"].initial = json.dumps(initial, indent=2)
				except Exception:
					self.fields["activities_table"].initial = "[]"

				# Provide friendly widgets/choices for icon and color fields
				if 'icon' in self.fields:
					self.fields['icon'].widget = forms.Select(choices=DAY_ICON_CHOICES)
				if 'color' in self.fields:
					self.fields['color'].widget = forms.Select(choices=DAY_COLOR_CHOICES)

				# If creating a new inline (no instance.pk) prefill friendly defaults
				if not getattr(self.instance, 'pk', None):
					if 'icon' in self.fields:
						self.fields['icon'].initial = DEFAULT_DAY_ICON
					if 'color' in self.fields:
						self.fields['color'].initial = DEFAULT_DAY_COLOR
					if 'date' in self.fields:
						# default to today's date for easier entry
						self.fields['date'].initial = datetime.date.today()

			def clean(self):
				cleaned = super().clean()
				raw = cleaned.get("activities_table", "")
				try:
					cleaned["activities"] = json.loads(raw) if raw else []
				except Exception:
					cleaned["activities"] = []
				return cleaned

		form = SummitAgendaDayForm

		def activities_table(self, obj):
			activities = getattr(obj, "activities", [])
			rows = ""
			for act in activities:
				time = act.get("time", "")
				title = act.get("title", "")
				rows += f"""
				<tr>
					<td><input type='text' value='{time}' class='activity-time' placeholder='08:00 - 09:00'></td>
					<td><input type='text' value='{title}' class='activity-title' placeholder='Session Title'></td>
					<td><button type='button' class='remove-row'>×</button></td>
				</tr>
				"""

			if not rows:
				rows = "<tr><td colspan='3' style='text-align:center;color:#777;'>No activities yet</td></tr>"

			return mark_safe(f"""
				<div class='activities-editor'>
					<table class='activity-table' style='width:100%;border-collapse:collapse;margin-bottom:8px;'>
						<thead>
							<tr style='background:#f3f3f3;'>
								<th style='width:25%;text-align:left;padding:6px;'>Time</th>
								<th style='width:65%;text-align:left;padding:6px;'>Title</th>
								<th style='width:10%;'></th>
							</tr>
						</thead>
						<tbody>{rows}</tbody>
					</table>
					<button type='button' class='add-row'>➕ Add Activity</button>
					<input type='hidden' name='activities_table' class='activities-hidden'>
				</div>

				<script>
				(function() {{
					const container = document.currentScript.closest('.activities-editor');
					const addBtn = container.querySelector('.add-row');
					const table = container.querySelector('tbody');
					const hidden = container.querySelector('.activities-hidden');

					function syncHidden() {{
						const activities = Array.from(table.querySelectorAll('tr')).map(tr => {{
							const time = tr.querySelector('.activity-time')?.value || '';
							const title = tr.querySelector('.activity-title')?.value || '';
							return {{time, title}};
						}}).filter(a => a.time || a.title);
						hidden.value = JSON.stringify(activities);
					}}

					addBtn.onclick = function() {{
						const row = document.createElement('tr');
						row.innerHTML = `
							<td><input type='text' class='activity-time' placeholder='08:00 - 09:00'></td>
							<td><input type='text' class='activity-title' placeholder='Session Title'></td>
							<td><button type='button' class='remove-row'>×</button></td>
						`;
						table.appendChild(row);
						syncHidden();
					}};

					table.addEventListener('click', e => {{
						if(e.target.classList.contains('remove-row')) {{
							e.target.closest('tr').remove();
							syncHidden();
						}}
					}});

					table.addEventListener('input', syncHidden);
					addBtn.addEventListener('click', syncHidden);
					syncHidden();
				}})();
				</script>
			""")

		activities_table.short_description = "Activities (Editable List)"

		def activities_display(self, obj):
			acts = getattr(obj, 'activities', None)
			if isinstance(acts, list) and acts:
				return ", ".join(a.get('title', '') for a in acts[:3])
			return ''
		activities_display.short_description = "Activities"

	inlines = [SummitAgendaDayInline]
    
    
class SummitAgendaItemInline(admin.TabularInline):
    model = SummitAgendaItem
    extra = 1  # number of empty forms shown
    fields = ('start_time', 'end_time', 'title')


@admin.register(SummitAgendaDay)
class SummitAgendaDayAdmin(admin.ModelAdmin):
    list_display = ('icon', 'location', 'date')
    inlines = [SummitAgendaItemInline]

    def icon(self, obj):
        return format_html("<i class='fas fa-clock' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''