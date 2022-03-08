import factory
from factory.django import DjangoModelFactory

from assisted_tagging.models import (
    AssistedTaggingModel,
    AssistedTaggingModelVersion,
    AssistedTaggingModelPredictionTag,
    DraftEntry,
    AssistedTaggingPrediction,
    WrongPredictionReview,
    MissingPredictionReview,
)


class AssistedTaggingModelFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Model-{n}')

    class Meta:
        model = AssistedTaggingModel


class AssistedTaggingModelVersionFactory(DjangoModelFactory):
    version = factory.Sequence(lambda n: f'version-{n}')

    class Meta:
        model = AssistedTaggingModelVersion


class AssistedTaggingModelPredictionTagFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f'name-{n}')
    tag_id = factory.Sequence(lambda n: f'tag-{n}')

    class Meta:
        model = AssistedTaggingModelPredictionTag


class DraftEntryFactory(DjangoModelFactory):
    class Meta:
        model = DraftEntry


class AssistedTaggingPredictionFactory(DjangoModelFactory):
    class Meta:
        model = AssistedTaggingPrediction


class WrongPredictionReviewFactory(DjangoModelFactory):
    class Meta:
        model = WrongPredictionReview


class MissingPredictionReviewFactory(DjangoModelFactory):
    class Meta:
        model = MissingPredictionReview
