import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from .models import (
    AnalysisFramework,
    Section,
    Widget,
    Filter,
)


class AnalysisFrameworkFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'AF-{n}')
    description = factory.Faker('sentence', nb_words=20)

    class Meta:
        model = AnalysisFramework


class SectionFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Section-{n}')

    class Meta:
        model = Section


class WidgetFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Widget-{n}')
    key = factory.Sequence(lambda n: f'widget-key-{n}')
    widget_id = fuzzy.FuzzyChoice(Widget.WidgetType.choices, getter=lambda c: c[0])
    properties = {}
    version = 1

    class Meta:
        model = Widget


class AfFilterFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Widget-filter-{n}')
    key = factory.Sequence(lambda n: f'widget-filter-key-{n}')
    properties = {}

    class Meta:
        model = Filter
