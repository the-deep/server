import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from gallery.factories import FileFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from .models import Entry


class EntryFactory(DjangoModelFactory):
    entry_type = fuzzy.FuzzyChoice(Entry.TagType)
    excerpt = fuzzy.FuzzyText(length=100)
    image = factory.SubFactory(FileFactory)
    analysis_framework = factory.SubFactory(AnalysisFrameworkFactory)

    class Meta:
        model = Entry
