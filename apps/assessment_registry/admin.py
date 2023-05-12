from django.contrib import admin

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
)


# Register your models here.
class MethodologyAttributeInline(admin.TabularInline):
    model = MethodologyAttribute
    extra = 1


@admin.register(AssessmentRegistry)
class AssessmentRegistryAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead', 'project')

    inlines = [
        MethodologyAttributeInline
    ]
