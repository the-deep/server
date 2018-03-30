from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import (
    AssessmentTemplate,

    MetadataGroup,
    MetadataField,
    MetadataOption,

    MethodologyGroup,
    MethodologyField,
    MethodologyOption,

    Sector,
    Focus,
    AffectedGroup,

    PrioritySector,
    PriorityIssue,
    SpecificNeedGroup,
    AffectedLocation,

    Assessment,
)


admin.site.register(AssessmentTemplate)
admin.site.register(MetadataGroup)
admin.site.register(MethodologyGroup)
admin.site.register(Sector)
admin.site.register(Focus)
admin.site.register(AffectedGroup)
admin.site.register(PrioritySector)
admin.site.register(PriorityIssue)
admin.site.register(SpecificNeedGroup)
admin.site.register(AffectedLocation)


class MetadataOptionInline(admin.StackedInline):
    model = MetadataOption


class MethodologyOptionInline(admin.StackedInline):
    model = MethodologyOption


@admin.register(MetadataField)
class MetadataFieldAdmin(admin.ModelAdmin):
    inlines = [MetadataOptionInline]


@admin.register(MethodologyField)
class MethodologyFieldAdmin(admin.ModelAdmin):
    inlines = [MethodologyOptionInline]


@admin.register(Assessment)
class AssessmentAdmin(VersionAdmin):
    pass
