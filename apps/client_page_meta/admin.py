from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Page


@admin.register(Page)
class PageAdmin(VersionAdmin):
    search_fields = ('title', 'page_id')
    list_display = ('title', 'page_id', 'help_url')
