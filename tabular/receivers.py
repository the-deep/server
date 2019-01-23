from django.db import models
from django.dispatch import receiver

from tabular.models import Field


@receiver(models.signals.pre_save, sender=Field)
def on_field_saved(sender, **kwargs):
    """
    The purpose of this receiver is to update the row value types
    in tabular sheet model whenever field type changes
    """
    field = kwargs.get('instance')
    if not field.id:
        return

    if field.type == field.current_type:
        return

    updated_data = field.sheet.cast_data_to(field)

    field.sheet.data = updated_data
    field.sheet.save()
