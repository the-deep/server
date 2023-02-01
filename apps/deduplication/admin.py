from django.contrib import admin

from .models import LSHIndex


@admin.register(LSHIndex)
class LSHIndexAdmin(admin.ModelAdmin):
    pass
