from django.db import models
from django.dispatch import receiver

from tabular.models import Field
from tabular.utils import get_geos_dict, get_geos_codes_from_geos_names


@receiver(models.signals.pre_save, sender=Field)
def on_field_saved(sender, **kwargs):
    """
    The purpose of this receiver is to update the row value types
    in tabular sheet model whenever field type changes
    """
    field = kwargs.get('instance')
    if field is None or not field.id:
        return

    if field.type == field.current_type and \
            field.options == field.current_options:
        return

    geos_names = geos_codes = {}
    if field.type == Field.GEO:
        geos_names = get_geos_dict(field.sheet.book.project)
        geos_codes = get_geos_codes_from_geos_names(geos_names)
    cast_info = field.cast_data(geos_names, geos_codes)

    field.data = cast_info['values']

    field.options = cast_info['options']
    # But don't save here, will cause recursion
    # field.save()
