import factory
from factory.django import DjangoModelFactory

from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry,
    DiscardedEntry,
)


class AnalysisFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Analysis-{n}')

    class Meta:
        model = Analysis


class AnalysisPillarFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Analysis-Pillar-{n}')
    main_statement = factory.Faker('sentence', nb_words=20)
    information_gap = factory.Faker('sentence', nb_words=20)

    class Meta:
        model = AnalysisPillar


class AnalyticalStatementFactory(DjangoModelFactory):
    statement = factory.Faker('sentence', nb_words=20)
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = AnalyticalStatement


class DiscardedEntryFactory(DjangoModelFactory):
    class Meta:
        model = DiscardedEntry


class AnalyticalStatementEntryFactory(DjangoModelFactory):
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = AnalyticalStatementEntry
