from django.contrib import admin

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    Question,
    Answer,
    ScoreRating,
    ScoreAnalyticalDensity,
    Summary,
    SummarySubPillarIssue,
    SummaryFocus,
    SummarySubDimensionIssue,
    SummaryIssue,
)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'sector', 'question')
    readonly_fields = ('created_by', 'modified_by', 'client_id',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        else:
            obj.modified_by = request.user
        super().save_model(request, obj, form, change)


class MethodologyAttributeInline(admin.TabularInline):
    model = MethodologyAttribute
    extra = 0
    exclude = ('created_by', 'modified_by', 'client_id')


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    exclude = ('created_by', 'modified_by', 'client_id')


class ScoreInline(admin.TabularInline):
    model = ScoreRating
    extra = 0
    exclude = ('created_by', 'modified_by', 'client_id')


class AnalyticalDensityInline(admin.TabularInline):
    model = ScoreAnalyticalDensity
    extra = 0
    exclude = ('created_by', 'modified_by', 'client_id')


class SummaryInline(admin.TabularInline):
    model = Summary
    extra = 0
    exclude = ('created_by', 'modified_by', 'client_id')


class SummarySubPillarIssueInline(admin.TabularInline):
    model = SummarySubPillarIssue
    extra = 0
    exclude = ('created_by', 'modified_by', 'client_id')


class SummaryFocusInline(admin.TabularInline):
    model = SummaryFocus
    extra = 0
    exclude = ('created_by', 'modified_by', 'client_id')


class SummarySubDimensionIssueInline(admin.TabularInline):
    model = SummarySubDimensionIssue
    extra = 0
    exclude = ('created_by', 'modified_by', 'client_id')


# TODO: Readonly mode
@admin.register(SummaryIssue)
class SummaryIssueAdmin(admin.ModelAdmin):
    pass


@admin.register(AssessmentRegistry)
class AssessmentRegistryAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead', 'project', 'coordinated_joint')

    inlines = [
        MethodologyAttributeInline,
        ScoreInline,
        AnalyticalDensityInline,
        AnswerInline,
        SummarySubPillarIssueInline,
        SummaryFocusInline,
        SummarySubDimensionIssueInline,
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('project', 'lead')
