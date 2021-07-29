import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from .models import (
    AnalysisFramework,
    Section,
    Widget,
)


class AnalysisFrameworkFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'AF-{n}')
    description = factory.Faker('sentence', nb_words=20)

    class Meta:
        model = AnalysisFramework


class SectionFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Section-{n}')
    analysis_framework = factory.SubFactory(AnalysisFrameworkFactory)

    class Meta:
        model = Section


class WidgetFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Widget-{n}')
    analysis_framework = factory.SubFactory(AnalysisFrameworkFactory)
    key = factory.Sequence(lambda n: f'widget-key-{n}')
    widget_id = fuzzy.FuzzyChoice(Widget.WidgetType.choices, getter=lambda c: c[0])
    properties = {}

    class Meta:
        model = Widget
