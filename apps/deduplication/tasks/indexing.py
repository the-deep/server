import pickle
from django.db import transaction
from django.utils import timezone
from celery import shared_task
from celery.utils.log import get_task_logger
from datasketch import LeanMinHash, MinHashLSH

from utils.decorators import log_time, warn_on_exception
from utils.common import batched
from lead.models import Lead
from project.models import Project
from deduplication.models import LSHIndex
from deduplication.utils import get_minhash, insert_to_index

logger = get_task_logger(__name__)


def find_and_set_duplicate_leads(index: MinHashLSH, lead: Lead, minhash: LeanMinHash):
    duplicate_lead_ids = index.query(minhash)
    duplicate_leads = Lead.objects.filter(pk__in=duplicate_lead_ids)
    lead.duplicate_leads.set(duplicate_leads)


def process_and_index_lead(lead: Lead, index: MinHashLSH):
    minhash = get_minhash(lead.leadpreview.text_extract)
    insert_to_index(index, lead.id, minhash)
    lead.is_indexed = True
    lead.indexed_at = timezone.now()
    lead.save(update_fields=['is_indexed', 'indexed_at'])

    find_and_set_duplicate_leads(index, lead, minhash)
    return index


def process_and_index_leads(
    project: Project,
    index_obj: LSHIndex,
):
    # Fetch leads which have been extracted and which have not been indexed
    leads = Lead.objects.filter(
        project=project,
        is_indexed=False,
    )
    index: MinHashLSH = index_obj.index
    try:
        batches = batched(leads, batch_size=200)
        for i, batch in enumerate(batches):
            with transaction.atomic():
                for lead in batch:
                    process_and_index_lead(lead, index)

                logger.info("processed batch", i)
                # Update the index
                index_obj.index = index
                index_obj.save()
    except Exception:
        logger.warning(
            f"Error creating index for project {project.title}({project.id})",
            exc_info=True
        )
        import traceback

        index_obj.has_errored = True
        index_obj.error = traceback.format_exc()
        index_obj.save(update_fields=['has_errored', 'error'])
    else:
        index_obj.status = LSHIndex.IndexStatus.CREATED
        index_obj.save(update_fields=['status'])


def create_project_index(project: Project):
    """
    Index all the unindexed leads in the project
    """
    index_obj = get_index_object_for_project(project)

    if index_obj.has_errored:
        logger.warning(f"")
        return

    process_and_index_leads(project, index_obj)


@shared_task
def create_indices():
    for project in Project.objects.all():
        with log_time(f'Indexing project({project.id}) "{project.title}"'):
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
@warn_on_exception(logger)
def index_lead_and_calculate_duplicates(lead: Lead):
    text = lead.leadpreview.text_extract
    if not text:
        return

    index_obj = get_index_object_for_project(lead.project)
    if index_obj.has_errored:
        # TODO: Re-create index? or just ignore?
        return

    index = process_and_index_lead(lead, index_obj.index)
    index_obj.index = index

    index_obj.save(update_fields=['index_pickle'])


@shared_task
def remove_lead_from_index(lead: Lead):
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
