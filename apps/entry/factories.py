import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from gallery.factories import FileFactory

from .models import Entry


class EntryFactory(DjangoModelFactory):
    entry_type = fuzzy.FuzzyChoice(Entry.TagType)
    excerpt = fuzzy.FuzzyText(length=100)
    image = factory.SubFactory(FileFactory)

    class Meta:
        model = Entry