import json
from typing import List, Dict, Tuple, NewType, Optional
from functools import reduce

from elasticsearch import Elasticsearch as Es
from elasticsearch.exceptions import RequestError


import logging

logger = logging.getLogger(__name__)

VectorDict = NewType('VectorDict', Dict[str, List[float]])
ErrorString = Optional[str]


class IndexAlreadyExists(Exception):
    def __init__(self, index_name, *args, **kwargs):
        return super().__init__(f'The index "{index_name}" already exists')


# Filter response data attributes
FILTER_PATH = ['hits.hits._score', 'hits.hits._id', 'hits.hits._source', 'hits.total', 'hits.max_score']


def create_data(doc_id: int, vectors: Dict[str, List[float]], index_name: str):
    data: List[Dict] = []
    data.append(dict(index=dict(_index=index_name, _id=doc_id)))
    data.append({vector_name: vector for vector_name, vector in vectors.items()})
    return data


def es_bulk(index_name: str, data: List[Dict], es: Es) -> Tuple[bool, str]:
    response = es.bulk(index=index_name, body=data)
    if response['errors']:
        return False, response['items'] and response['items'][0]['index']['error']['caused_by']['reason']
    return True, 'Success'


def add_to_index(doc_id: int, vectors: VectorDict, index_name: str, es: Es):
    data = create_data(doc_id, vectors, index_name)
    return es_bulk(index_name, data, es)


def add_to_index_bulk(doc_ids: List[int], vectors: List[VectorDict], index_name: str, es: Es) -> Tuple[bool, str]:
    # Check if lengths match
    if len(doc_ids) != len(vectors):
        return False, "Mismatching number of doc_ids and vectors"
    data: List[Dict] = reduce(
        lambda acc, id_vector: [*acc, *create_data(id_vector[0], id_vector[1], index_name)],
        zip(doc_ids, vectors),
        []
    )
    return es_bulk(index_name, data, es)


def search_similar(similar_count: int, vector: Tuple[str, List[float]], index_name: str, es: Es):
    query = {
        "size": similar_count,
        "query": {
            "knn": {
                vector[0]: {
                    "vector": vector[1],
                    "k": similar_count
                }
            }
        }
    } if vector else None
    return es.search(body=query, index=index_name, filter_path=FILTER_PATH)


def index_exists(index_name: str, es: Es) -> bool:
    """
    Checks if index named `index_name` exists
    """
    return es.indices.exists(index_name)


def create_knn_vector_index_if_not_exists(
        index_name: str, vector_size: int, es: Es
        ) -> Tuple[bool, ErrorString]:
    return create_knn_vector_index(index_name, vector_size, es, ignore_error=True)


def create_knn_vector_index(
        index_name: str, vector_size: int, es: Es, ignore_error: bool = False
        ) -> Tuple[bool, ErrorString]:
    """
    Create knn vector index with given `index_name` and `vector_size`.
    The vector name will be `vector1`
    """
    if es.indices.exists(index_name):
        if ignore_error:
            return True, None
        return False, f"The index '{index_name}' already exists"

    properties = dict(
        vector1=dict(
            type="knn_vector",
            dimension=vector_size
        )
    )
    data = dict(
        settings={"index": {"knn": True, "knn.space_type": "cosinesimil"}},
        mappings=dict(
            properties=properties
        )
    )

    try:
        es.indices.create(index_name, body=data)
        return True, None
    except RequestError as e:
        if e.args[1] == 'resource_already_exists_exception':
            return False, f"The index '{index_name}' already exists"
        reason = e.args[2]['error']['root_cause'][0]['reason']
        logger.warning(reason)
        return False, reason
