from django.db import models


class DeeplTrackBaseModel(models.Model):
    """
    Provide basic fields which are consistent between NLP related models
    """

    class Status(models.IntegerChoices):
        PENDING = 0, "Pending"
        STARTED = 1, "Started"  # INITIATED in deepl side
        SUCCESS = 2, "Success"
        FAILED = 3, "Failed"
        SEND_FAILED = 4, "Send Failed"

    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.PENDING)

    class Meta:
        abstract = True
