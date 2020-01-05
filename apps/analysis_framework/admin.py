from django.contrib import admin
from deep.admin import linkify
from analysis_framework.models import (
    AnalysisFramework,
    AnalysisFrameworkRole,
    AnalysisFrameworkMembership,
    Widget, Filter,
    Exportable,
)

from questionnaire.models import (
    FrameworkQuestion,
)

from deep.admin import (
    VersionAdmin,
    StackedInline,
    query_buttons,
    ModelAdmin as JFModelAdmin,
)


class AnalysisFrameworkMemebershipInline(admin.TabularInline):
    model = AnalysisFrameworkMembership
    extra = 0
    autocomplete_fields = ('added_by', 'member',)


class WidgetInline(StackedInline):
    model = Widget


class FilterInline(StackedInline):
    model = Filter


class ExportableInline(StackedInline):
    model = Exportable


class FrameworkQuestionInline(StackedInline):
    model = FrameworkQuestion


class AFRelatedAdmin(JFModelAdmin):
    search_fields = ('title',)
    list_display = (
        '__str__', linkify('analysis_framework'),
    )
    autocomplete_fields = ('analysis_framework',)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('analysis_framework')

    def has_add_permission(self, request, obj=None):
        return False


for model in [Widget, Filter, Exportable, FrameworkQuestion]:
    admin.site.register(model, AFRelatedAdmin)


@admin.register(AnalysisFramework)
class AnalysisFrameworkAdmin(VersionAdmin):
    readonly_fields = ['is_private']
    inlines = [AnalysisFrameworkMemebershipInline]
    search_fields = ('title',)
    custom_inlines = [
        ('widget', WidgetInline),
        ('filter', FilterInline),
        ('exportable', ExportableInline),
        ('framework_question', FrameworkQuestionInline),
    ]
    list_display = [
        'title',  # 'project_count',
        query_buttons('View', [inline[0] for inline in custom_inlines]),
    ]
    autocomplete_fields = ('created_by', 'modified_by',)

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        for name, inline in self.custom_inlines:
            if request.GET.get(f'show_{name}', 'False').lower() == 'true':
                inlines.append(inline(self.model, self.admin_site))
        return inlines

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AnalysisFrameworkRole)
class AnalysisFrameworkRoleAdmin(admin.ModelAdmin):
    readonly_fields = ['is_private_role']

    def has_add_permission(self, request, obj=None):
        return False
