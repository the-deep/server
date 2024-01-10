from collections import defaultdict

from promise import Promise
from django.utils.functional import cached_property
from django.db import models
from project.models import Project

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    Widget,
    Section,
    Filter,
    Exportable,
    AnalysisFrameworkMembership,
    AnalysisFramework,
)


class WidgetLoader(DataLoaderWithContext):
    @staticmethod
    def load_widgets(keys, parent, **filters):
        qs = Widget.objects\
            .filter(
                **{
                    f'{parent}__in': keys,
                    **filters,
                }
            ).exclude(widget_id__in=Widget.DEPRECATED_TYPES)\
            .annotate(conditional_parent_widget_type=models.F('conditional_parent_widget__widget_id'))\
            .order_by('order', 'id')
        _map = defaultdict(list)
        for widget in qs:
            _map[getattr(widget, f'{parent}_id')].append(widget)
        return Promise.resolve([_map[key] for key in keys])

    def batch_load_fn(self, keys):
        return self.load_widgets(keys, 'analysis_framework')


class SecondaryWidgetLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        return WidgetLoader.load_widgets(keys, 'analysis_framework', section__isnull=True)


class SectionWidgetLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        return WidgetLoader.load_widgets(keys, 'section')


class SectionLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = Section.objects.filter(analysis_framework__in=keys).order_by('order', 'id')
        _map = defaultdict(list)
        for section in qs:
            _map[section.analysis_framework_id].append(section)
        return Promise.resolve([_map[key] for key in keys])


class FilterLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = Filter.qs_with_widget_type().filter(
            analysis_framework__in=keys,
            widget_type__isnull=False,  # Remove if widget_type is empty (meaning widget doesn't exists)
        )
        _map = defaultdict(list)
        for _filter in qs:
            _map[_filter.analysis_framework_id].append(_filter)
        return Promise.resolve([_map[key] for key in keys])


class ExportableLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = Exportable.qs_with_widget_type().filter(
            analysis_framework__in=keys,
            widget_type__isnull=False,  # Remove if widget_type is empty (meaning widget doesn't exists)
        )
        _map = defaultdict(list)
        for exportable in qs:
            _map[exportable.analysis_framework_id].append(exportable)
        return Promise.resolve([_map[key] for key in keys])


class MembershipLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisFrameworkMembership.objects\
            .filter(framework__in=keys)\
            .select_related('role', 'member', 'added_by')
        _map = defaultdict(list)
        for section in qs:
            _map[section.framework_id].append(section)
        return Promise.resolve([_map[key] for key in keys])


class AnalysisFrameworkTagsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisFramework.tags.through.objects.filter(
            analysisframework__in=keys,
        ).select_related('analysisframeworktag')
        _map = defaultdict(list)
        for row in qs:
            _map[row.analysisframework_id].append(row.analysisframeworktag)
        return Promise.resolve([_map[key] for key in keys])


class AnalysisFrameworkProjectCountLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        stat_qs = Project.objects\
            .filter(analysis_framework__in=keys)\
            .order_by('analysis_framework').values('analysis_framework')\
            .annotate(
                project_count=models.functions.Coalesce(
                    models.Count(
                        'id',
                        filter=models.Q(is_test=False)
                    ),
                    0,
                ),
                test_project_count=models.functions.Coalesce(
                    models.Count(
                        'id',
                        filter=models.Q(is_test=True)
                    ),
                    0,
                ),
            ).values('analysis_framework', 'project_count', 'test_project_count')
        _map = {
            stat.pop('analysis_framework'): stat
            for stat in stat_qs
        }
        _dummy = {
            'project_count': 0,
            'test_project_count': 0,
        }
        return Promise.resolve([_map.get(key, _dummy) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def secondary_widgets(self):
        return SecondaryWidgetLoader(context=self.context)

    @cached_property
    def sections(self):
        return SectionLoader(context=self.context)

    @cached_property
    def sections_widgets(self):
        return SectionWidgetLoader(context=self.context)

    @cached_property
    def filters(self):
        return FilterLoader(context=self.context)

    @cached_property
    def exportables(self):
        return ExportableLoader(context=self.context)

    @cached_property
    def members(self):
        return MembershipLoader(context=self.context)

    @cached_property
    def af_tags(self):
        return AnalysisFrameworkTagsLoader(context=self.context)

    @cached_property
    def af_project_count(self):
        return AnalysisFrameworkProjectCountLoader(context=self.context)
