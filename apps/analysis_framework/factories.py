import factory
from django.core.files.base import ContentFile
from factory import fuzzy
from factory.django import DjangoModelFactory

from .models import AnalysisFramework, AnalysisFrameworkTag, Filter, Section, Widget
from .widgets.store import widget_store


class AnalysisFrameworkTagFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f"AF-Tag-{n}")
    description = factory.Faker("sentence", nb_words=20)
    icon = factory.LazyAttribute(
        lambda n: ContentFile(factory.django.ImageField()._make_data({"width": 100, "height": 100}), f"example_{n.title}.png")
    )

    class Meta:
        model = AnalysisFrameworkTag


class AnalysisFrameworkFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f"AF-{n}")
    description = factory.Faker("sentence", nb_words=20)

    class Meta:
        model = AnalysisFramework

    @factory.post_generation
    def tags(self, create, extracted, **_):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class SectionFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f"Section-{n}")

    class Meta:
        model = Section


class WidgetFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f"Widget-{n}")
    key = factory.Sequence(lambda n: f"widget-key-{n}")
    widget_id = fuzzy.FuzzyChoice(widget_store.keys())
    properties = {}
    version = 1

    class Meta:
        model = Widget


class AfFilterFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f"Widget-filter-{n}")
    key = factory.Sequence(lambda n: f"widget-filter-key-{n}")
    properties = {}

    class Meta:
        model = Filter
