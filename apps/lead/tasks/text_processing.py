import os
import hashlib
from typing import List, Tuple, Optional
from typing_extensions import TypedDict
import langdetect


from deep_utils.dynamodb.models import Source
from deep_utils.deduplication.vector_generator import create_trigram_vector, SUPPORTED_LANGUAGES
from deep_utils.deduplication.elasticsearch import search_similar
from deep_utils.deduplication.utils import es_wrapper, remove_puncs_and_extra_spaces

from gallery.models import File

import logging
logger = logging.getLogger(__file__)

DEDUPLICATION_LAMBDA_ENDPOINT = os.environ.get('DEDUPLICATION_LAMBDA_ENDPOINT')
SIMILAR_FETCH_COUNT = 20
SIMILARITY_THRESHOLD = 0.9

ErrorString = Optional[str]


class LeadIdSimilarity(TypedDict):
    lead_id: str
    similarity_score: float


# NOTE: environment variable 'SOURCE_TABLE_NAME' should be defined, used internally by deep_utils.dynamodb
def get_source_extract_from_pynamodb(source_key):
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


def get_duplicate_leads(lead_data: dict) -> Tuple[List[LeadIdSimilarity], ErrorString]:
    source_key = get_source_key(lead_data)
    project = lead_data['project']

    extract = get_source_extract_from_pynamodb(source_key)
    if not extract:
        # TODO: probably raise error telling source is not yet extracted
        return [], None

    lang = langdetect.detect(extract)
    if lang not in SUPPORTED_LANGUAGES:
        return [], None

    es = es_wrapper(DEDUPLICATION_LAMBDA_ENDPOINT)
    vector = create_trigram_vector(remove_puncs_and_extra_spaces(extract))
    index_name = f'{project}-{lang}-index'

    similar_response = search_similar(SIMILAR_FETCH_COUNT, dict(vector1=vector), index_name, es)
    hits = similar_response['hits']
    if hits['max_score'] < SIMILARITY_THRESHOLD:
        return [], None

    similar_leads = [
        dict(lead_id=x['_id'], similarity_score=x['_score'])
        for x in hits['hits']
        if x['_score'] > SIMILARITY_THRESHOLD
    ]
    return similar_leads, None
