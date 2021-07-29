from collections import defaultdict

from promise import Promise
from django.utils.functional import cached_property

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    Widget,
    Section,
    AnalysisFrameworkMembership,
)


class WidgetLoader(DataLoaderWithContext):
    @staticmethod
    def load_widgets(keys, parent, **filters):
        qs = Widget.objects.filter(
            **{
                f'{parent}__in': keys,
                **filters,
            }
        ).order_by('order', 'id')
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


class MembershipLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisFrameworkMembership.objects\
            .filter(framework__in=keys)\
            .select_related('role', 'member', 'added_by')
        _map = defaultdict(list)
        for section in qs:
            _map[section.framework_id].append(section)
        return Promise.resolve([_map[key] for key in keys])


class DataLoaders(WithContextMixin):
    # @cached_property
    # def widgets(self):
    #     return WidgetLoader(context=self.context)

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
    def members(self):
        return MembershipLoader(context=self.context)
