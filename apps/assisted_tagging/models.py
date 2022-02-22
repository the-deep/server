from django.db import models

from user.models import User


class NlpModel(models.Model):
    nlp_id = models.CharField(max_length=256)
    active_version = models.ForeignKey(
        'assisted_tagging.NlpModelVersion', null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name


class NlpModelVersion(models.Model):
    model = models.ForeignKey(NlpModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    endpoint = models.CharField(max_length=256)
    mlflow_uri = models.CharField(max_length=256)
    metric_params = models.JSONField()
    date = models.DateTimeField()
    version = models.CharField(max_length=256)  # 'MAJOR.MINOR.PATCH'

    def __str__(self):
        return self.name


class NlpModelPredictionTag(models.Model):
    name = models.CharField(max_length=256)
    nlp_id = models.FloatField()
    is_depricated = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ModelPrediction(models.Model):
    model_version = models.ForeignKey(NlpModelVersion, on_delete=models.CASCADE)
    entry = models.ForeignKey('entry.Entry', on_delete=models.CASCADE)
    prediction = models.FloatField()
    threshold = models.FloatField()
    tag = models.ForeignKey(PredictionEnum, on_delete=models.CASCADE, null=True, blank=True, related_name="tag")
    category = models.ForeignKey(PredictionEnum, on_delete=models.CASCADE, null=True, blank=True, related_name="category")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id


class ReviewTag(models.Model):
    class ReviewTypes(models.IntegerChoices):
        WRONG_TAG = 1, 'Wrong Tag'
        MISSING_TAG = 2, 'Missing Tag'

    model_prediction = models.ForeignKey(ModelPrediction, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    review_type = models.FloatField(choices=ReviewTypes.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.review_type
