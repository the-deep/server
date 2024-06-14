# Reusable actions
from deduplication.tasks.indexing import remove_lead_from_index
from django.db import models, transaction
from django.dispatch import receiver
from lead.models import Lead, LeadDuplicates
from unified_connector.models import ConnectorSourceLead


@receiver(models.signals.post_delete, sender=Lead)
def unset_already_added_connector_lead(sender, instance, **kwargs):
    if instance.connector_lead is None:
        return
    ConnectorSourceLead.update_aleady_added_using_lead(instance, added=False)


@receiver(models.signals.pre_delete, sender=Lead)
def update_indices(sender, instance, **kwargs):
    transaction.on_commit(lambda: update_index_and_duplicates(instance))


def update_index_and_duplicates(lead: Lead):
    remove_lead_from_index.delay(lead.id)
    # Now get all other leads which are duplicates of the lead and update their count
    dup_qs1 = LeadDuplicates.objects.filter(source_lead=lead.id).values_list("target_lead", flat=True)
    dup_qs2 = LeadDuplicates.objects.filter(target_lead=lead.id).values_list("source_lead", flat=True)
    dup_leads = Lead.objects.filter(pk__in=dup_qs1.union(dup_qs2))
    dup_leads.update(duplicate_leads_count=models.F("duplicate_leads_count") - 1)
