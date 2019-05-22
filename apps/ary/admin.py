from django.contrib import admin
from reversion.admin import VersionAdmin

from deep.admin import linkify

from .models import (
    AssessmentTemplate,

    MetadataGroup,
    MetadataOption,

    MethodologyGroup,
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

    ScoreQuestionnaireSector,
    ScoreQuestionnaireSubSector,
    ScoreQuestionnaire,

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


class ScoreQuestionnaireSubSectorInline(admin.TabularInline):
    model = ScoreQuestionnaireSubSector
    extra = 0


class ScoreQuestionnaireInline(admin.TabularInline):
    model = ScoreQuestionnaire
    extra = 0


@admin.register(ScoreQuestionnaireSector)
class ScoreQuestionnaireSectorAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'method', 'sub_method', linkify('template'))
    inlines = [ScoreQuestionnaireSubSectorInline]


@admin.register(ScoreQuestionnaireSubSector)
class ScoreQuestionnaireSubSectorAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', linkify('sector'), linkify('sector.template'))
    inlines = [ScoreQuestionnaireInline]


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
