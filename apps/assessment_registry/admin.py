from django.contrib import admin

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    Summary,
    Question,
    Answer,
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
