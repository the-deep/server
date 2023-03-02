import pickle
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from celery import shared_task
from celery.utils.log import get_task_logger
from datasketch import LeanMinHash, MinHashLSH

from utils.common import batched
from lead.models import Lead
from project.models import Project
from deduplication.models import LSHIndex
from deduplication.utils import get_minhash, insert_to_index

logger = get_task_logger(__name__)


def find_and_set_duplicate_leads(index: MinHashLSH, lead: Lead, minhash: LeanMinHash):
    duplicate_lead_ids = index.query(minhash)
    duplicate_leads_qs = Lead.objects.filter(pk__in=duplicate_lead_ids)
    duplicate_leads_count = duplicate_leads_qs.count()
    if duplicate_leads_count > 0:
        lead.duplicate_leads_count += duplicate_leads_count
        duplicate_leads_qs\
            .update(duplicate_leads_count=F('duplicate_leads_count') + 1)
    lead.duplicate_leads.set(duplicate_leads_qs)
    lead.save(update_fields=['duplicate_leads_count'])


def process_and_index_lead(lead: Lead, index: MinHashLSH):
    text = lead.leadpreview.text_extract if hasattr(lead, 'leadpreview') else lead.text
    if not text:
        return index
    minhash = get_minhash(text)
    find_and_set_duplicate_leads(index, lead, minhash)

    insert_to_index(index, lead.id, minhash)
    lead.is_indexed = True
    lead.indexed_at = timezone.now()
    lead.save(update_fields=['is_indexed', 'indexed_at'])
    return index


def process_and_index_leads(
    project: Project,
    index_obj: LSHIndex,
):
    # Fetch leads which have been extracted and which have not been indexed
    leads_qs = Lead.objects.filter(
        project=project,
        is_indexed=False,
    )
    index: MinHashLSH = index_obj.index
    try:
        batches = batched(leads_qs, batch_size=200)
        for batch in batches:
            with transaction.atomic():
                for lead in batch:
                    process_and_index_lead(lead, index)
                # Update the index
                index_obj.index = index
                index_obj.save()
    except Exception:
        logger.error(
            f"Error creating index for project {project.title}({project.id})",
            exc_info=True
        )

        index_obj.has_errored = True
        index_obj.save(update_fields=['has_errored'])
    else:
        index_obj.status = LSHIndex.IndexStatus.CREATED
        index_obj.save(update_fields=['status'])


def create_project_index(project: Project):
    """
    Index all the unindexed leads in the project
    """
    index_obj = get_index_object_for_project(project)

    if index_obj.has_errored:
        logger.error(f"Errored index object, LSHIndex id {index_obj.id}. Aborting.")
        return

    process_and_index_leads(project, index_obj)


@shared_task
def create_indices():
    for project in Project.objects.all():
        create_project_index(project)


def get_index_object_for_project(project: Project) -> LSHIndex:
    index_obj, created = LSHIndex.objects.get_or_create(
        project=project,
        defaults={
            "name": project.title,
            "pickle_version": pickle.format_version,
        },
    )

    if created:
        # MinHashLSH object will not be initialized during the creation, create it
        index = MinHashLSH(
            threshold=LSHIndex.THRESHOLD,
            num_perm=LSHIndex.NUM_PERM,
        )
        index_obj.index = index
        index_obj.save()
    return index_obj


@shared_task
def index_lead_and_calculate_duplicates(lead_id: int):
    lead = Lead.objects.filter(id=lead_id).first()
    if lead is None:
        logger.error(f"Cannot index inexistent lead(id={lead_id})")
        return

    text = lead.leadpreview.text_extract if hasattr(lead, 'leadpreview') else lead.text
    if not text:
        return

    index_obj = get_index_object_for_project(lead.project)
    if index_obj.has_errored:
        # TODO: Re-create index? or just ignore?
        logger.warning(f"LSHIndex object has errored. object id {index_obj.id}")
        return

    index = process_and_index_lead(lead, index_obj.index)
    index_obj.index = index

    index_obj.save(update_fields=['index_pickle'])


@shared_task
def remove_lead_from_index(lead_id: int):
    lead = Lead.objects.filter(id=lead_id).first()
    if lead is None:
        logger.warning(f"Cannot remove inexistent lead(id={lead_id}) from index")
        return
    index_obj = get_index_object_for_project(lead.project)

    if index_obj.has_errored:
        logger.warning(f"Attempt to remove lead from errored index for project {lead.project.id}")
        return
    index = index_obj.index
    if index is None:
        logger.warning(f"Attempt to remove lead from inexistent index for project {lead.project.id}")
        return
    index.remove(lead.id)
    index_obj.index = index
    index_obj.save(update_fields=['index_pickle'])
