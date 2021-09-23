from django.db import models
from django.dispatch import receiver

from lead.models import Lead
from .models import Entry


@receiver(models.signals.post_save, sender=Entry)
def update_lead_status(sender, instance, created, **kwargs):
    lead = instance.lead
    if lead.status != Lead.Status.IN_PROGRESS:
        lead.status = Lead.Status.IN_PROGRESS
        lead.save(update_fields=['status'])
