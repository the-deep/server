from django.dispatch import receiver
from django.db import models

from .models import Entry


@receiver(models.signals.post_save, sender=Entry)
def on_entry_saved(sender, **kwargs):
    lead = kwargs.get('instance').lead
    # TODO After `project` is added to Entry
    # this should not use lead
    lead.project.update_status()
