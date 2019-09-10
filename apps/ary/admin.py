from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from reversion.admin import VersionAdmin

from deep.admin import linkify

from .management.commands.export_ary_template import export_ary_fixture
from .models import (
    AssessmentTemplate,

    MetadataField,
    MetadataGroup,
    MetadataOption,

    MethodologyField,
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
class AnalysisFrameworkTemplateAdmin(VersionAdmin):
    change_list_template = 'ary/ary_change_list.html'
    search_fields = ('title',)
    inlines = [ScoreBucketInline]
    autocomplete_fields = ('created_by', 'modified_by',)

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                'export/', self.admin_site.admin_view(self.export_ary),
                name='{}_{}_export'.format(*info)
            ),
        ] + super().get_urls()

    def export_ary(self, request):
        content = export_ary_fixture()
        return HttpResponse(content, content_type='application/json')


class MetadataOptionInline(admin.TabularInline):
    model = MetadataOption
    extra = 0


class MethodologyOptionInline(admin.TabularInline):
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


class FieldAdminMixin():
    list_display = ('title', 'order', linkify('group'),)


@admin.register(MetadataField)
class MetadataFieldAdmin(FieldAdminMixin, admin.ModelAdmin):
    inlines = [MetadataOptionInline]


@admin.register(MethodologyField)
class MethodologyFieldAdmin(FieldAdminMixin, admin.ModelAdmin):
    inlines = [MethodologyOptionInline]


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
