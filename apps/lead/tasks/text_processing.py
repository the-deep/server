import os
import hashlib
from typing import List, Tuple, Optional
import requests
# from celery import shared_task
# import langdetect

# from deep_utils.deduplication.vector_generator import create_trigram_vector
# from deep_utils.deduplication.elasticsearch import add_to_index, search_similar
# from deep_utils.deduplication.utils import es_wrapper

from gallery.models import File

import logging
logger = logging.getLogger(__file__)

DEDUPLICATION_LAMBDA_ENDPOINT = os.environ.get('DEDUPLICATION_LAMBDA_ENDPOINT')

ErrorString = Optional[str]


def get_duplicate_leads(lead_data: dict) -> Tuple[List[int], ErrorString]:
    # Create source key from website url or attachment(s3) url which will then be
    # passed to lambda to check for duplicate_leads
    source_key = None
    attachment = lead_data.get('attachment')
    url = lead_data.get('url')
    project = lead_data['project']
    if attachment:
        gallery_file = File.objects.filter(id=attachment.get('id')).first()
        if gallery_file is None:
            return [], None

        s3url = gallery_file.file.url
        source_key = f's3::{s3url}'

    elif url:
        source_key = hashlib.sha224(url.encode()).hexdigest()

    url = f'{DEDUPLICATION_LAMBDA_ENDPOINT}?source_key={source_key}&project={project}'
    response = requests.get(url)
    if response.status_code != 200:
        logger.warning(f'Non OK response from deduplication lambda: {response.text}')
        return [], "Error response from server"
    results: List[int] = response.json()['results']
    return results, None
