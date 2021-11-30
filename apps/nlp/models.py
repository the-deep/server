from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class ModelInfo(models.Model):
    name = models.CharField(max_length=256)
    endpoint = models.CharField(max_length=256)
    mlflow_uri = models.CharField(max_length=256)
    metric_params = JSONField()
    date = models.DateTimeField()
    version = models.FloatField(default=0.1)

    def __str__(self):
        return self.name


class PredictionEnum(models.Model):
    name = models.CharField(max_length=256)
    value = models.FloatField()

    def __str__(self):
        return self.name


class ModelPrediction(models.Model):

    entry = models.ForeignKey('entry.Entry', on_delete=models.CASCADE)
    model_info = models.ForeignKey('nlp.ModelInfo', null=True, blank=True, on_delete=models.CASCADE)
    prediction = models.FloatField(verbose_name=_('Prediction'))
    threshold = models.FloatField(verbose_name=_('Threshold'))
    version = models.FloatField(default=0.1)
    tag = models.ForeignKey('nlp.PredictionEnum', on_delete=models.CASCADE, null=True, blank=True, related_name="tag")
    category = models.ForeignKey(
        'nlp.PredictionEnum', on_delete=models.CASCADE, null=True, blank=True, related_name="category"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id


class ReviewTag(models.Model):

    class ReviewTypes(models.IntegerChoices):
        WRONG_TAG = 1, _('Wrong Tag')
        MISSING_TAG = 2, _('Missing Tag')

    model_prediction = models.ForeignKey(
        ModelPrediction, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Model prediction')
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('User')
    )
    review_type = models.FloatField(verbose_name=_('Review Type'), choices=ReviewTypes.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.review_type
