from django.contrib import admin

from .models import AssessmentRegistry

# Register your models here.


@admin.register(AssessmentRegistry)
class AssessmentRegistryAdmin(admin.ModelAdmin):
    list_display = ('id',)
