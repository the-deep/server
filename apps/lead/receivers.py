from django.db import models, transaction
from django.dispatch import receiver

from lead.models import Lead, LeadPreview, LeadPreviewImage
from lead.tasks import remove_lead_from_index


@receiver(models.signals.post_save, sender=Lead)
def on_lead_saved(sender, **kwargs):
    instance = kwargs.get('instance')
    instance.project.update_status()


@receiver(models.signals.pre_delete, sender=Lead)
def cleanup_on_lead_delete(sender, instance, **kwargs):
    """
    NOTE: If s3 files needs to be deleted make sure gallery file is not used by another lead (or any other entity)
        - can occur due to lead copy
        - can occur due to category editor
    """
    id = instance.id
    project_id = instance.project_id
    transaction.on_commit(lambda: remove_lead_from_index(id, project_id))


@receiver(models.signals.post_delete, sender=LeadPreview)
@receiver(models.signals.post_delete, sender=LeadPreviewImage)
def cleanup_file_on_instance_delete(sender, instance, **kwargs):
    files_to_delete = []
    for field in instance._meta.get_fields():
        if isinstance(field, models.FileField):
            field_name = field.name
            value = getattr(instance, field_name)
            if not value:
                continue
            files_to_delete.append([value.storage, value.name])
    transaction.on_commit(
        lambda: [
            storage.delete(path) for storage, path in files_to_delete
        ]
    )
