from django.db import transaction, models
from django.dispatch import receiver

from deduplication.models import LSHIndex
from lead.models import Lead, LeadDuplicates


@receiver(models.signals.post_delete, sender=LSHIndex)
def set_leads_as_unindexed(sender, instance, **kwargs):
    # set leads is_indexed False
    transaction.on_commit(
        lambda: clear_duplicates(instance)
    )


@transaction.atomic
def clear_duplicates(index_obj: LSHIndex):
    index = index_obj.index
    if index is None:
        return
    lead_ids = list(index.keys)
    Lead.objects.filter(id__in=lead_ids).update(
        is_indexed=False,
        duplicate_leads_count=0,
    )

    LeadDuplicates.objects.filter(
        models.Q(source_lead_id__in=lead_ids) |
        models.Q(target_lead_id__in=lead_ids)
    ).delete()
