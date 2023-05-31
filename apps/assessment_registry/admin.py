from django.contrib import admin

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    Summary,
)


# Register your models here.
class MethodologyAttributeInline(admin.TabularInline):
    model = MethodologyAttribute
    extra = 1


class SummaryInline(admin.TabularInline):
    model = Summary


@admin.register(AssessmentRegistry)
class AssessmentRegistryAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead', 'project')

    inlines = [
        MethodologyAttributeInline,
        SummaryInline,
    ]
