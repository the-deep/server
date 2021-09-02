import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from gallery.factories import FileFactory
from user.factories import UserFactory

from .models import Entry, Attribute


class EntryFactory(DjangoModelFactory):
    entry_type = fuzzy.FuzzyChoice(Entry.TagType)
    excerpt = fuzzy.FuzzyText(length=100)
    image = factory.SubFactory(FileFactory)
    controlled_changed_by = factory.SubFactory(UserFactory)
    controlled = False

    class Meta:
        model = Entry

    @factory.post_generation
    def verified_by(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for verified_by_user in extracted:
                self.verified_by.add(verified_by_user)


class EntryAttriuteFactory(DjangoModelFactory):
    pass

    class Meta:
        model = Attribute
