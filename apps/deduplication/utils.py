import re
from datasketch import MinHash, LeanMinHash

from deduplication.models import LSHIndex


def preprocess_text(txt: str):
    # Remove punctuations and lowercase
    return re.sub(r"[^a-z ]", "", txt).lower()


def get_minhash(txt: str) -> LeanMinHash:
    processed = preprocess_text(txt)
    items = set(processed.split())
    h = MinHash(num_perm=LSHIndex.NUM_PERM)
    for item in items:
        h.update(item.encode("utf8"))
    return LeanMinHash(h)


def insert_to_index(index, lead_id, lead_hash: LeanMinHash):
    try:
        index.insert(lead_id, lead_hash)
    except ValueError:
        pass
