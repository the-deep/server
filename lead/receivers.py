from django.db import models
from django.dispatch import receiver

from lead.models import Lead


@receiver(models.signals.post_save, sender=Lead)
def on_lead_saved(sender, **kwargs):
    instance = kwargs.get('instance')
    project = None
    if instance:
        project = instance.project

    if project:
        project.update_status()
