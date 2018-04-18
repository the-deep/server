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

    ScorePillar,
    ScoreQuestion,
    ScoreScale,
    ScoreMatrixPillar,
    ScoreMatrixRow,
    ScoreMatrixColumn,
    ScoreMatrixScale,

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
admin.site.register(ScoreScale)


class MetadataOptionInline(admin.StackedInline):
    model = MetadataOption
    extra = 0


class MethodologyOptionInline(admin.StackedInline):
    model = MethodologyOption
    extra = 0


@admin.register(MetadataField)
class MetadataFieldAdmin(admin.ModelAdmin):
    inlines = [MetadataOptionInline]


@admin.register(MethodologyField)
class MethodologyFieldAdmin(admin.ModelAdmin):
    inlines = [MethodologyOptionInline]


class ScoreQuestionInline(admin.TabularInline):
    model = ScoreQuestion
    extra = 0


@admin.register(ScorePillar)
class ScorePillarAdmin(admin.ModelAdmin):
    inlines = [ScoreQuestionInline]


class ScoreMatrixRowInline(admin.TabularInline):
    model = ScoreMatrixRow
    extra = 0


class ScoreMatrixColumnInline(admin.TabularInline):
    model = ScoreMatrixColumn
    extra = 0


class ScoreMatrixScaleInline(admin.TabularInline):
    model = ScoreMatrixScale
    extra = 0


@admin.register(ScoreMatrixPillar)
class ScoreMatrixPillarAdmin(admin.ModelAdmin):
    inlines = [ScoreMatrixRowInline,
               ScoreMatrixColumnInline,
               ScoreMatrixScaleInline]


@admin.register(Assessment)
class AssessmentAdmin(VersionAdmin):
    pass
