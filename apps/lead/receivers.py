# Reusable actions
from django.db import models, transaction
from django.dispatch import receiver

from lead.models import Lead
from unified_connector.models import ConnectorSourceLead
from deduplication.tasks.indexing import remove_lead_from_index


@receiver(models.signals.post_delete, sender=Lead)
def unset_already_added_connector_lead(sender, instance, **kwargs):
    if instance.connector_lead is None:
        return
    ConnectorSourceLead.update_aleady_added_using_lead(instance, added=False)


@receiver(models.signals.post_delete, sender=Lead)
def remove_lead_from_index_after_deletion(sender, instance, **kwargs):
    transaction.on_commit(lambda: remove_lead_from_index.delay(instance.id))
