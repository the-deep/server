from django.db import models
from django.db.transaction import on_commit
from django.dispatch import receiver

from lead.models import (
    Lead,
    LeadPreview,
    LeadPreviewImage,
)


@receiver(models.signals.post_save, sender=Lead)
def on_lead_saved(sender, **kwargs):
    instance = kwargs.get('instance')
    instance.project.update_status()


@receiver(models.signals.post_delete, sender=LeadPreview)
@receiver(models.signals.post_delete, sender=LeadPreviewImage)
def cleanup_file_on_instance_delete(sender, instance, **kwargs):
    images = []
    for field in instance._meta.get_fields():
        if isinstance(field, models.FileField):
            field_name = field.name
            field_value = getattr(instance, field_name)
            if not field_value:
                continue
            storage, path = field_value.storage, field_value.name
            images.append([storage, path])
    on_commit(lambda: [storage.delete(path) for storage, path in images])
