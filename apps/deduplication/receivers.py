from django.db import transaction, models
from django.dispatch import receiver

from deduplication.models import LSHIndex
from lead.models import Lead


@receiver(models.signals.post_delete, sender=LSHIndex)
def set_leads_as_unindexed(sender, instance, **kwargs):
    index = instance.index
    lead_ids = list(index.keys)
    # set leads is_indexed False
    transaction.on_commit(
        lambda: Lead.objects.filter(id__in=lead_ids).update(is_indexed=False)
    )
