from django.contrib import admin
from deep.admin import VersionAdmin, linkify

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
    UnderlyingFactor,

    PrioritySector,
    PriorityIssue,
    SpecificNeedGroup,
    AffectedLocation,

    ScoreBucket,
    ScorePillar,
    ScoreQuestion,
    ScoreScale,
    ScoreMatrixPillar,
    ScoreMatrixRow,
    ScoreMatrixColumn,
    ScoreMatrixScale,

    Assessment,
)


class ScoreBucketInline(admin.TabularInline):
    model = ScoreBucket
    extra = 0


@admin.register(AssessmentTemplate)
class AnalysisFrameworkAdmin(VersionAdmin):
    inlines = [ScoreBucketInline]


class MetadataOptionInline(admin.StackedInline):
    model = MetadataOption
    extra = 0


class MethodologyOptionInline(admin.StackedInline):
    model = MethodologyOption
    extra = 0


class ScoreQuestionInline(admin.TabularInline):
    model = ScoreQuestion
    extra = 0


class ScoreMatrixRowInline(admin.TabularInline):
    model = ScoreMatrixRow
    extra = 0


class ScoreMatrixColumnInline(admin.TabularInline):
    model = ScoreMatrixColumn
    extra = 0


class ScoreMatrixScaleInline(admin.TabularInline):
    model = ScoreMatrixScale
    extra = 0


@admin.register(ScorePillar)
class ScorePillarAdmin(admin.ModelAdmin):
    inlines = [ScoreQuestionInline]
    list_display = ('title', linkify('template'), 'order', 'weight')


@admin.register(ScoreMatrixPillar)
class ScoreMatrixPillarAdmin(admin.ModelAdmin):
    inlines = [ScoreMatrixRowInline, ScoreMatrixColumnInline, ScoreMatrixScaleInline]
    list_display = ('title', linkify('template'), 'order', 'weight')


class FieldAdminMixin():
    search_fields = ('title', 'group__title')
    list_filter = ('group__title',)
    list_display = ('title', linkify('group', 'title'), linkify('group__template'))


@admin.register(MetadataField)
class MetadataFieldAdmin(FieldAdminMixin, admin.ModelAdmin):
    inlines = [MetadataOptionInline]


@admin.register(MethodologyField)
class MethodologyFieldAdmin(FieldAdminMixin, admin.ModelAdmin):
    inlines = [MethodologyOptionInline]


@admin.register(AffectedGroup)
class AffectedGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', linkify('template'),)


class TemplateGroupAdminMixin():
    search_fields = ('title', 'template__title')
    list_display = ('title', linkify('template'),)
    list_filter = ('template',)


@admin.register(Focus)
class FocusAdmin(TemplateGroupAdminMixin, admin.ModelAdmin):
    pass


@admin.register(UnderlyingFactor)
class UnderlyingFactorAdmin(TemplateGroupAdminMixin, admin.ModelAdmin):
    pass


@admin.register(MetadataGroup)
class MetadataGroupAdmin(TemplateGroupAdminMixin, admin.ModelAdmin):
    pass


@admin.register(MethodologyGroup)
class MethodologyGroupAdmin(TemplateGroupAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Sector)
class SectorAdmin(TemplateGroupAdminMixin, admin.ModelAdmin):
    pass


@admin.register(PrioritySector)
class PrioritySectorAdmin(TemplateGroupAdminMixin, admin.ModelAdmin):
    pass


@admin.register(PriorityIssue)
class PriorityIssueAdmin(TemplateGroupAdminMixin, admin.ModelAdmin):
    pass


@admin.register(SpecificNeedGroup)
class SpecificNeedGroupAdmin(TemplateGroupAdminMixin, admin.ModelAdmin):
    pass


@admin.register(AffectedLocation)
class AffectedLocationAdmin(TemplateGroupAdminMixin, admin.ModelAdmin):
    pass


@admin.register(ScoreScale)
class ScoreScaleAdmin(TemplateGroupAdminMixin, admin.ModelAdmin):
    pass


@admin.register(Assessment)
class AssessmentAdmin(VersionAdmin):
    search_fields = ('lead__title',)
    list_display = ('lead', linkify('project'),)
