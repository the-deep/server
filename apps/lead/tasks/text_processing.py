import os
import hashlib
from typing import List, Tuple, Optional, NewType
from typing_extensions import TypedDict
import langdetect


from deep_utils.dynamodb.models import Source
from deep_utils.deduplication.vector_generator import create_trigram_vector, SUPPORTED_LANGUAGES
from deep_utils.deduplication.elasticsearch import (
    search_similar,
    create_knn_vector_index_if_not_exists,
    add_to_index,
    Es,  # This is just the type
)
from deep_utils.deduplication.utils import es_wrapper, remove_puncs_and_extra_spaces

from gallery.models import File


import logging
logger = logging.getLogger(__file__)

DEDUPLICATION_ES_ENDPOINT = os.environ.get('DEDUPLICATION_ES_ENDPOINT')
DEDUPLICATION_ES_STAGE = os.environ.get('DEDUPLICATION_ES_STAGE', 'local')
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
            self, vector: List[float] = None, es: Es = None, error: str = None,
            lang: str = None, similar_leads: List[LeadIdSimilarity] = None, index_name: str = None):
        self.vector = vector
        self.es = es
        self.lang = lang
        self.similar_leads = similar_leads
        self.error = error
        self.index_name = index_name


# NOTE: environment variable 'SOURCE_TABLE_NAME' should be defined, used internally by deep_utils.dynamodb
def get_source_extract_from_pynamodb(source_key: Optional[str]) -> Optional[str]:
    if not source_key:
        return None
    source = Source.get(source_key)
    if source is None:
        return None
    return source.extract.simplified_text


def get_source_key(lead_data: dict) -> Optional[str]:
    attachment = lead_data.get('attachment')
    url = lead_data.get('url')
    if attachment:
        gallery_file = File.objects.filter(id=attachment.get('id')).first()
        if gallery_file is None:
            return None
        s3url = gallery_file.file.url
        return f's3::{s3url}'
    if url:
        return hashlib.sha224(url.encode()).hexdigest()
    return None


def get_duplicate_leads(lead_data: dict) -> LeadDuplicationInfo:
    source_key = get_source_key(lead_data)
    project = lead_data['project'].id
    return get_duplicate_leads_source_key_project(source_key, project)


def get_duplicate_leads_source_key_project(source_key: Optional[str], project: int) -> LeadDuplicationInfo:
    extract = get_source_extract_from_pynamodb(source_key)
    # TODO: check status of source extraction
    if not extract:
        # TODO: probably raise error telling source is not yet extracted
        return LeadDuplicationInfo()

    lang = langdetect.detect(extract)
    es = es_wrapper(DEDUPLICATION_ES_ENDPOINT)
    lead_duplication_info = LeadDuplicationInfo(es=es, lang=lang)
    if lang not in SUPPORTED_LANGUAGES:
        return lead_duplication_info

    vector = create_trigram_vector(lang, remove_puncs_and_extra_spaces(extract))
    lead_duplication_info.vector = vector
    logger.info(DEDUPLICATION_ES_STAGE, project, lang)
    index_name = f'{DEDUPLICATION_ES_STAGE}-{project}-{lang}-index'
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


def add_lead_to_index(lead, lead_duplication_info: LeadDuplicationInfo):
    vector_dict = dict(vector1=lead_duplication_info.vector)
    add_to_index(lead.id, vector_dict, lead_duplication_info.index_name, lead_duplication_info.es)
