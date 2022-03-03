# Reusable actions
from django.db import models
from django.dispatch import receiver

from lead.models import Lead
from unified_connector.models import ConnectorSourceLead


@receiver(models.signals.post_delete, sender=Lead)
def unset_already_added_connector_lead(sender, instance, **kwargs):
    if instance.connector_lead is None:
        return
    ConnectorSourceLead.update_aleady_added_using_lead(instance, added=False)
