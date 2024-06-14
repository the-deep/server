import factory
from factory.django import DjangoModelFactory

from .models import EntryReviewComment, EntryReviewCommentText


class EntryReviewCommentFactory(DjangoModelFactory):
    class Meta:
        model = EntryReviewComment


class EntryReviewCommentTextFactory(DjangoModelFactory):
    text = factory.Sequence(lambda n: f"Text-{n}")

    class Meta:
        model = EntryReviewCommentText
