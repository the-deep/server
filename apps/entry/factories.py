import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from gallery.factories import FileFactory
from project.factories import ProjectFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from lead.factories import LeadFactory

from .models import Entry


class EntryFactory(DjangoModelFactory):
    entry_type = fuzzy.FuzzyChoice(Entry.TagType)
    excerpt = fuzzy.FuzzyText(length=100)
    image = factory.SubFactory(FileFactory)
    project = factory.SubFactory(ProjectFactory)
    analysis_framework = factory.SubFactory(AnalysisFrameworkFactory)
    lead = factory.SubFactory(LeadFactory)

    class Meta:
        model = Entry
