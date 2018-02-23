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

    AssessmentTopic,
    AffectedGroup,

    Assessment,
)


admin.site.register(AssessmentTemplate)
admin.site.register(MetadataGroup)
admin.site.register(MethodologyGroup)
admin.site.register(AssessmentTopic)
admin.site.register(AffectedGroup)


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
