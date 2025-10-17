from django.core.management.base import BaseCommand
from django.apps import apps
import re
import json
from datetime import datetime
import os


def is_binary_like(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    if '\x00' in s:
        return True
    up = s.upper()
    if 'JFIF' in up or 'ICC_PROFILE' in up or '\ufffd' in s:
        return True
    # high ratio of non-printables
    non_print = len(re.sub(r'[\x20-\x7E]', '', s))
    if non_print / max(1, len(s)) > 0.3:
        return True
    return False


class Command(BaseCommand):
    help = 'Scan text and JSON fields across installed models for binary-like content (report-only by default).'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100, help='Maximum rows to inspect per model')
        parser.add_argument('--apply', action='store_true', help='Apply fixes: backup and nullify offending fields')
        parser.add_argument('--backup', type=str, default=None, help='Path to write backup JSON file (defaults to ./binary_scan_backup_TIMESTAMP.json)')

    def handle(self, *args, **options):
        limit = options.get('limit', 100)
        apply_changes = options.get('apply', False)
        backup_path = options.get('backup')

        self.stdout.write('Scanning models for binary-like text...')

        findings = []

        for model in apps.get_models():
            textual_fields = [f for f in model._meta.get_fields() if getattr(f, 'get_internal_type', lambda: '')() in ('TextField', 'CharField', 'JSONField')]
            field_names = [f.name for f in textual_fields]
            if not field_names:
                continue
            qs = model.objects.all()[:limit]
            for obj in qs:
                for f in textual_fields:
                    fld = f.name
                    try:
                        val = getattr(obj, fld)
                    except Exception:
                        continue
                    if isinstance(val, str) and is_binary_like(val):
                        findings.append({'model': model.__name__, 'pk': getattr(obj, 'pk', None), 'field': fld, 'value_preview': val[:200]})
                    elif val is not None and not isinstance(val, str):
                        s = str(val)
                        if is_binary_like(s):
                            findings.append({'model': model.__name__, 'pk': getattr(obj, 'pk', None), 'field': fld, 'value_preview': s[:200], 'json': True})

        if not findings:
            self.stdout.write('No binary-like values found.')
            return

        # Print summary
        for f in findings:
            self.stdout.write(f"MODEL {f['model']} id={f['pk']} field={f['field']} looks binary-like")

        # Backup findings if requested or if applying changes
        if backup_path is None:
            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            backup_path = os.path.join(os.getcwd(), f'binary_scan_backup_{ts}.json')

        with open(backup_path, 'w', encoding='utf-8') as bf:
            json.dump(findings, bf, ensure_ascii=False, indent=2)
        self.stdout.write(f'Wrote backup of findings to {backup_path}')

        if apply_changes:
            self.stdout.write('Applying fixes: nullifying offending fields (reporting each change)')
            for f in findings:
                model = apps.get_model(app_label=f.get('model').split('.')[0] if '.' in f.get('model') else f.get('model').lower(), model_name=f['model'])
                # fallback: try to search by model name across apps
                if model is None:
                    for app_mod in apps.get_app_configs():
                        try:
                            model = app_mod.get_model(f['model'])
                            break
                        except Exception:
                            continue
                if model is None:
                    self.stdout.write(f"Could not resolve model for {f['model']}; skipping")
                    continue
                try:
                    obj = model.objects.get(pk=f['pk'])
                except Exception:
                    self.stdout.write(f"Failed to load {f['model']} pk={f['pk']}; skipping")
                    continue
                try:
                    # Nullify or blank the field safely depending on field type
                    field_obj = next((x for x in textual_fields if x.name == f['field']), None)
                    if field_obj is not None and getattr(field_obj, 'get_internal_type', lambda: '')() == 'JSONField':
                        setattr(obj, f['field'], None)
                    else:
                        # CharField/TextField: set empty string
                        try:
                            setattr(obj, f['field'], None)
                        except Exception:
                            try:
                                setattr(obj, f['field'], '')
                            except Exception:
                                pass
                    obj.save()
                    self.stdout.write(f"Cleared {f['model']} pk={f['pk']} field={f['field']}")
                except Exception as e:
                    self.stdout.write(f"Failed to clear {f['model']} pk={f['pk']} field={f['field']}: {e}")

        self.stdout.write('Scan complete. Review the backup before making further changes.')
