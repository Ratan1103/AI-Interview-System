from django.contrib import admin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'file', 'has_text')
    search_fields = ('user__username',)

    def has_text(self, obj):
        return bool(obj.extracted_text)
    has_text.boolean = True
    has_text.short_description = 'Text Extracted'
