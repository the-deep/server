from django.contrib import admin
from deep.admin import linkify
from questionnaire.models import (
    FrameworkQuestion,
)

from deep.admin import (
    VersionAdmin,
    StackedInline,
    query_buttons,
    ModelAdmin as JFModelAdmin,
)

from .models import (
    AnalysisFramework,
    AnalysisFrameworkTag,
    AnalysisFrameworkRole,
    AnalysisFrameworkMembership,
    Section,
    Widget,
    Filter,
    Exportable,
)
from admin_auto_filters.filters import AutocompleteFilterFactory


class WidgetInline(StackedInline):
    model = Widget


class FilterInline(StackedInline):
    model = Filter


class ExportableInline(StackedInline):
    model = Exportable


class FrameworkQuestionInline(StackedInline):
    model = FrameworkQuestion


class SectionInline(StackedInline):
    model = Section


class AFRelatedAdmin(JFModelAdmin):
    search_fields = ('analysis_framework__title', 'title',)
    list_display = (
        '__str__', linkify('analysis_framework'),
    )
    autocomplete_fields = ('analysis_framework',)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('analysis_framework')

    def has_add_permission(self, request, obj=None):
        return False


for model in [Section, Widget, Filter, Exportable, FrameworkQuestion]:
    admin.site.register(model, AFRelatedAdmin)


@admin.register(AnalysisFramework)
class AnalysisFrameworkAdmin(VersionAdmin):
    readonly_fields = ['is_private']
    inlines = [SectionInline, WidgetInline]
    search_fields = ('title',)
    list_filter = ('is_private', 'assisted_tagging_enabled',)
    custom_inlines = [
        ('filter', FilterInline),
        ('exportable', ExportableInline),
        ('framework_question', FrameworkQuestionInline),
    ]
    list_display = [
        'title',  # 'project_count',
        'created_at',
        'created_by',
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

    def get_formsets_with_inlines(self, request, obj=None):
        widget_queryset = Widget.objects.filter(analysis_framework=obj)
        for inline in self.get_inline_instances(request, obj):
            formset = inline.get_formset(request, obj)
            for field in ['widget', 'parent_widget', 'conditional_parent_widget']:
                if field not in formset.form.base_fields:
                    continue
                formset.form.base_fields[field].queryset = widget_queryset
            yield formset, inline


@admin.register(AnalysisFrameworkRole)
class AnalysisFrameworkRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'type', 'is_default_role')
    readonly_fields = ['is_private_role']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AnalysisFrameworkTag)
class AnalysisFrameworkTagAdmin(admin.ModelAdmin):
    list_display = ('id', 'title',)


@admin.register(AnalysisFrameworkMembership)
class AnalysisFrameworkMembershipAdmin(admin.ModelAdmin):
    search_fields = ('framework__title',)
    autocomplete_fields = ('added_by', 'member',)
    serch_fields = ['analysis_framework__title']
    list_display = ['framework', 'member', 'role']
    list_filter = (
        AutocompleteFilterFactory('Project', 'framework__project'),
        AutocompleteFilterFactory('AnalysisFramework', 'framework'),
        'framework__is_private'
    )

    def get_readonly_fields(self, request, obj=None):
        # editing an existing object
        if obj:
            return self.readonly_fields + ('framework', )
        return self.readonly_fields
