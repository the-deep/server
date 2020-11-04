# Document De-Duplication
> author: [@bewakes](https://github.com/bewakes)

A module for creating and indexing document character trigrams.

## A use case scenario
Suppose we have an elasticsearch index `my-index` setup in **AWS** with vector name `vector1` of size 10000
```python
from utils.deduplication.utils import es_wrapper
from utils.deduplication.vector_generator import create_trigram_vector
from utils.deduplication.elasticsearch import search_similar, add_to_index

es = es_wrapper('<aws endpoint>', 'aws_region')
text_document: str = 'this is test document'
vector = create_trigram_vector('en', text_document)

similar_docs_resp = search_similar(10, ('vector1', vector), 'my-index', es)

total = search_similar_resp['hits']['total']
max_score = search_similar_resp['hits']['max_score']
docs_ids = [x['_id'] for x in similar_docs_resp['hits']['hits']]
docs_scores = [x['_score'] for x in similar_docs_resp['hits']['hits']]


# To add document to index
resp = add_to_index(doc_id='1', vectors=dict(vector1=vector), index_name='my-index', es=es)
hasError = resp['errors']
```

## Motivation
Can be found [here](MOTIVATION.md)

## Scripts
There are [scripts](utils/deduplication/scripts) that generate trigrams from leads(documents) in DEEP.

## Modules
### trigrams
Just the collection of relevant trigrams for `en`, `es` and `fr` languages.

```python
from utils.deduplication.trigrams import en, es, fr

en_trigrams = en.trigrams  # [' th', 'the', 'he ', ....]
es_trigrams = es.trigrams
fr_trigrams = fr.trigrams
```
**NOTE**: The trigrams contain 10000 relevant trigrams. So, the vector created will have dimension 10000.

### utils
Consists of following functions:
```python
# This is a wrapper function for creating Elasticsearch object
es_wrapper(endpoint: str, region: str, profile_name: str = 'default') -> Elasticsearch`
```
```pytohn
remove_puncs_and_extra_spaces(text: str) -> str` which is used for preprocessing texts
```

### vector_generator
```python
create_trigram_vector(lang: str, text: str) -> List[float]
```
```python
create_count_vector(processed_text: str, trigrams: Dict[str, int]) -> List[int]
```
```python
normalize_count_vector(count_vector: List[int]) -> List[float]
```


### elasticsearch
```python
search_similar(similar_count: int, vector: Tuple[str, List[float]], index_name: str, es: Elasticsearch)
```
```python
add_to_index(doc_id: int, vectors: Dict[str, List[float]], index_name: str, es: Elasticsearch)
```
```python
index_exists(index_name: str, es: Es) -> bool
```
```python
create_knn_vector_index(index_name: str, vector_size: int, es: Es, ignore_error: bool = False) -> Tuple[bool, ErrorString]
```
```python
create_knn_vector_index_if_not_exists(index_name: str, vector_size: int, es: Es) -> Tuple[bool, ErrorString]
```
