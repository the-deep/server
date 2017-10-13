from django.db import models


class DummyData(models.Model):
    model_name = models.CharField(max_length=255)
    data_id = models.IntegerField()
    db_id = models.IntegerField()

    def __str__(self):
        return '{} - {} (DB ID: {})'.format(
            self.model_name,
            self.data_id,
            self.db_id,
        )
