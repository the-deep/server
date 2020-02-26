from django.contrib import admin

from .models import (
    CrisisType,
)


@admin.register(CrisisType)
class CrisisTypeAdmin(admin.ModelAdmin):
    pass
