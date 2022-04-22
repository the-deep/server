# from django.contrib.postgres.fields import ArrayField
from __future__ import annotations
from typing import Union
from django.db import models
from django.db.models.functions import Concat

from analysis_framework.models import Widget
from project.models import Project
from lead.models import Lead
from user_resource.models import UserResource, UserResourceCreated


class AssistedTaggingModel(models.Model):
    model_id = models.CharField(max_length=256)
    name = models.CharField(max_length=256)

    def __int__(self):
        self.versions: models.QuerySet[AssistedTaggingModelVersion]

    def __str__(self):
        return f'<{self.name}> {self.model_id}'

    @property
    def latest_version(self):
        return self.versions.order_by('-version').first()


class AssistedTaggingModelVersion(models.Model):
    model = models.ForeignKey(AssistedTaggingModel, on_delete=models.CASCADE, related_name='versions')
    version = models.CharField(max_length=256)  # 'MAJOR.MINOR.PATCH'
    # Extra attributes (TODO: Later)
    # endpoint = models.CharField(max_length=256)
    # mlflow_uri = models.CharField(max_length=256)
    # metric_params = models.JSONField()
    # date = models.DateTimeField()

    def __str__(self):
        return self.version

    @classmethod
    def get_latest_models_version(cls) -> models.QuerySet:
        return AssistedTaggingModelVersion.objects.annotate(
            model_with_version=Concat(
                models.F('model_id'), models.F('version'),
                output_field=models.CharField(),
            )
        ).filter(
            model_with_version__in=AssistedTaggingModelVersion.objects.order_by().values('model').annotate(
                max_version=models.Max('version'),
            ).annotate(
                model_with_version=Concat(
                    models.F('model_id'), models.F('max_version'),
                    output_field=models.CharField(),
                )
            ).values('model_with_version')
        ).order_by('model_with_version')


class AssistedTaggingModelPredictionTag(models.Model):
    name = models.CharField(max_length=256, blank=True)
    is_category = models.BooleanField(default=False)
    tag_id = models.CharField(max_length=256)
    group = models.CharField(max_length=256, blank=True, null=True)
    # Extra attributes
    hide_in_analysis_framework_mapping = models.BooleanField(default=False)
    is_category = models.BooleanField(default=False)
    is_deprecated = models.BooleanField(default=False)
    parent_tag = models.ForeignKey(
        'assisted_tagging.AssistedTaggingModelPredictionTag',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name


class DraftEntry(UserResourceCreated):
    class PredictionStatus(models.IntegerChoices):
        PENDING = 0, 'Pending'
        STARTED = 1, 'Started'
        DONE = 2, 'Done'
        SEND_FAILED = 3, 'Send Failed'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='+')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='+')
    excerpt = models.TextField()
    prediction_status = models.SmallIntegerField(choices=PredictionStatus.choices, default=PredictionStatus.PENDING)
    # After successfull prediction
    prediction_received_at = models.DateTimeField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.predictions: models.QuerySet[AssistedTaggingPrediction]
        self.missing_prediction_reviews: models.QuerySet[MissingPredictionReview]

    @classmethod
    def get_existing_draft_entry(cls, project: Project, lead: Lead, excerpt: str) -> Union[DraftEntry, None]:
        already_existing_draft_entry = cls.objects.filter(
            project=project,
            lead=lead,
            excerpt=excerpt,
        ).first()
        if (
            already_existing_draft_entry and
            not already_existing_draft_entry.predictions.filter(
                ~models.Q(model_version__in=AssistedTaggingModelVersion.get_latest_models_version()),
            ).exists()
        ):
            return already_existing_draft_entry

    def clear_data(self):
        self.predictions.all().delete()
        self.missing_prediction_reviews.all().delete()


class AssistedTaggingPrediction(models.Model):
    class DataType(models.IntegerChoices):
        RAW = 0, 'Raw'  # data is stored in value
        TAG = 1, 'Tag'  # data is stored in category + tag

    data_type = models.SmallIntegerField(choices=DataType.choices)

    model_version = models.ForeignKey(AssistedTaggingModelVersion, on_delete=models.CASCADE, related_name='+')
    draft_entry = models.ForeignKey(DraftEntry, on_delete=models.CASCADE, related_name='predictions')
    # For RAW DataType
    value = models.CharField(max_length=255, blank=True)
    # For Tag DataType
    category = models.ForeignKey(
        AssistedTaggingModelPredictionTag,
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
    )
    tag = models.ForeignKey(
        AssistedTaggingModelPredictionTag,
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
    )
    # If score is provided
    prediction = models.DecimalField(max_digits=22, decimal_places=20, null=True, blank=True)
    threshold = models.DecimalField(max_digits=22, decimal_places=20, null=True, blank=True)
    # Recommended by Model
    is_selected = models.BooleanField(default=False)
    # TODO: is_used = models.BooleanField(default=False)

    id: int

    def __str__(self):
        return self.id


class WrongPredictionReview(UserResource):
    prediction = models.ForeignKey(
        AssistedTaggingPrediction,
        on_delete=models.CASCADE,
        related_name='wrong_prediction_reviews',
    )
    client_id = None  # Removing field from UserResource

    id: int

    def __str__(self):
        return self.id


class MissingPredictionReview(UserResource):
    draft_entry = models.ForeignKey(DraftEntry, on_delete=models.CASCADE, related_name='missing_prediction_reviews')
    category = models.ForeignKey(AssistedTaggingModelPredictionTag, on_delete=models.CASCADE, related_name="+")
    tag = models.ForeignKey(AssistedTaggingModelPredictionTag, on_delete=models.CASCADE, related_name="+")
    client_id = None  # Removing field from UserResource

    id: int

    def __str__(self):
        return self.id


# ------------------------ Analysis Framework ---------------------------------------------
class PredictionTagAnalysisFrameworkWidgetMapping(models.Model):
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE)
    tag = models.ForeignKey(
        AssistedTaggingModelPredictionTag,
        on_delete=models.CASCADE,
        null=True,  # For just enabling assisted tagging for a widget. For eg: geo/number/date/datetime widgets
        blank=True,
    )
    association = models.JSONField(null=True, blank=True)