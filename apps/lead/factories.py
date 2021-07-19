import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from project.factories import ProjectFactory
from gallery.factories import FileFactory
from .models import Lead


class LeadFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Lead-{n}')
    text = fuzzy.FuzzyText(length=100)
    project = factory.SubFactory(ProjectFactory)
    attachment = factory.SubFactory(FileFactory)

    class Meta:
        model = Lead
