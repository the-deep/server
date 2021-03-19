from django.db import models
from django.db.transaction import on_commit
from django.dispatch import receiver

from lead.models import Lead, LeadPreview, LeadPreviewImage


# @receiver(models.signals.post_delete, sender=LeadPreview)
# @receiver(models.signals.post_delete, sender=LeadPreviewImage)
def cleanup_file_on_instance_delete(sender, instance, **kwargs):
    for field in instance._meta.get_fields():
        if isinstance(field, models.FileField):
            field_name = field.name
            field_value = getattr(instance, field_name)
            if not field_value:
                continue
            storage, path = field_value.storage, field_value.name

            def delete_files():
                storage.delete(path)

            on_commit(delete_files)
