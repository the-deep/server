import logging
import langdetect

from django.conf import settings

from deep_serverless.models.source_extract import Source
from deep_utils.deduplication.vector_generator import create_trigram_vector, SUPPORTED_LANGUAGES
from deep_utils.deduplication.elasticsearch import (
    search_similar,
    create_knn_vector_index_if_not_exists,
    add_to_index,
    Es,  # This is just the type
)
from deep_utils.deduplication.utils import es_wrapper, remove_puncs_and_extra_spaces

from typing import List, Optional
from typing_extensions import TypedDict

from lead.models import Lead
from gallery.models import File

logger = logging.getLogger(__file__)

SIMILAR_FETCH_COUNT = 20
SIMILARITY_THRESHOLD = 0.9
VECTOR_SIZE = 10000
VECTOR_NAME = 'vector1'  # KNN Vector name

ErrorString = Optional[str]


class LeadIdSimilarity(TypedDict):
    lead_id: str
    similarity_score: float


class LeadDuplicationInfo:
    def __init__(
        self,
        source: Source = None,
        vector: List[float] = None,
        es: Es = None, error: str = None,
        lang: str = None,
        similar_leads: List[LeadIdSimilarity] = None,
        index_name: str = None,
    ):
        self.source = source
        self.vector = vector
        self.es = es
        self.lang = lang
        self.similar_leads = similar_leads
        self.error = error
        self.index_name = index_name


def get_es_index_name(project_id: int, lang: str) -> str:
    # NOTE: Changing this format can lead to data loss
    return f'{settings.DEDUPLICATION_ES_STAGE}-{project_id}-{lang}-index'


def get_source_from_pynamodb(attachment_id: Optional[int] = None, url: Optional[str] = None) -> Optional[Source]:
    """
    Source: Pynamodb instance (Maintained by github.com/the-deep/serverless)
    """
    try:
        if attachment_id:
            attachment = File.objects.filter(id=attachment_id).first()
            return attachment and Source.get(Source.get_s3_key(attachment.file.name))
        elif url:
            return Source.get(Source.get_url_hash(url))
    except Source.DoesNotExist:
        pass
    return None


def get_source_from_pynamodb_for_lead(lead: Lead) -> Optional[Source]:
    return get_source_from_pynamodb(lead.attachment_id, lead.url)


def get_duplicate_leads_in_project_for_source(project: int, source: Optional[Source]) -> LeadDuplicationInfo:
    extract = source and source.extract.simplified_text
    # TODO: check status of source extraction
    if not extract:
        # TODO: probably raise error telling source is not yet extracted
        return LeadDuplicationInfo(source=source)

    lang = langdetect.detect(extract)
    es = es_wrapper(settings.DEDUPLICATION_ES_ENDPOINT)
    lead_duplication_info = LeadDuplicationInfo(source=source, es=es, lang=lang)
    if lang not in SUPPORTED_LANGUAGES:
        return lead_duplication_info

    vector = create_trigram_vector(lang, remove_puncs_and_extra_spaces(extract))
    lead_duplication_info.vector = vector
    logger.info(settings.DEDUPLICATION_ES_STAGE, project, lang)
    index_name = get_es_index_name(project, lang)
    lead_duplication_info.index_name = index_name

    create_knn_vector_index_if_not_exists(index_name, VECTOR_SIZE, es)
    similar_response = search_similar(SIMILAR_FETCH_COUNT, (VECTOR_NAME, vector), index_name, es)
    hits = similar_response['hits']
    max_score = hits['max_score'] or 0  # this can be None
    if max_score < SIMILARITY_THRESHOLD:
        return lead_duplication_info

    lead_duplication_info.similar_leads = [
        dict(lead_id=x['_id'], similarity_score=x['_score'])
        for x in hits['hits']
        if x['_score'] > SIMILARITY_THRESHOLD
    ]
    return lead_duplication_info


def add_lead_to_index(lead: Lead, lead_duplication_info: LeadDuplicationInfo):
    vector_dict = dict(vector1=lead_duplication_info.vector)
    add_to_index(lead.id, vector_dict, lead_duplication_info.index_name, lead_duplication_info.es)


def remove_lead_from_index(lead_id: int, project_id: int):
    if settings.DEDUPLICATION_ES_ENDPOINT is None:
        return
    es = es_wrapper(settings.DEDUPLICATION_ES_ENDPOINT)
    # Remove lead data for each language (if exists)
    data = [
        {
            'delete': {'_id': lead_id, '_index': get_es_index_name(project_id, lang)}
        } for lang in SUPPORTED_LANGUAGES
    ]
    es.bulk(data)
