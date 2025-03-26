import json
from django.contrib.sessions.models import Session
from django.contrib import admin
from django.utils.safestring import mark_safe

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'expire_date', 'get_decoded']
    readonly_fields = ['session_key', 'session_data', 'expire_date', 'get_decoded']

    def get_decoded(self, obj):
        data = obj.get_decoded()
        pretty_data = json.dumps(data, indent=4, ensure_ascii=False)
        return mark_safe(f'<pre>{pretty_data}</pre>')

    get_decoded.short_description = "Session Data (decoded)"
