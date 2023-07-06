from django.contrib import admin

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    Question,
    Answer,
    SummaryIssue,
    ScoreRating,
    ScoreAnalyticalDensity,
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


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question')
    readonly_fields = ('created_by', 'modified_by', 'client_id',)


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


@admin.register(AssessmentRegistry)
class AssessmentRegistryAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead', 'project')

    inlines = [
        MethodologyAttributeInline,
        ScoreInline,
        AnalyticalDensityInline,
        AnswerInline,
    ]


admin.site.register(SummaryIssue)
