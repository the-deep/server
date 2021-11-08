import factory
from factory.django import DjangoModelFactory

from .models import (
    Analysis,
    AnalyticalStatement,
    AnalyticalStatementEntry,
    DiscardedEntry,
)


class AnalysisFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Analysis-{n}')
    main_statement = factory.Faker('sentence', nb_words=20)
    information_gap = factory.Faker('sentence', nb_words=20)

    class Meta:
        model = Analysis


class AnalyticalStatementFactory(DjangoModelFactory):
    statement = factory.Faker('sentence', nb_words=20)
    order = factory.Sequence()

    class Meta:
        model = AnalyticalStatement


class DiscardedEntryFactory(DjangoModelFactory):
    class Meta:
        model = DiscardedEntry


class AnalyticalStatementEntryFactory(DjangoModelFactory):
    order = factory.Sequence()

    class Meta:
        model = AnalyticalStatementEntry
