from typing import List, Dict

from .utils import remove_puncs_and_extra_spaces
from .trigrams import en, es, fr

import logging

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = ['en', 'es', 'fr']

EN_TRIGRAMS = {t: i for i, t in enumerate(en.trigrams)}
ES_TRIGRAMS = {t: i for i, t in enumerate(es.trigrams)}
FR_TRIGRAMS = {t: i for i, t in enumerate(fr.trigrams)}


class InvalidText(Exception):
    pass


class InvalidLanguage(Exception):
    pass


class TrigramsNotLoaded(Exception):
    pass


def create_count_vector(processed_text: str, trigrams: Dict[str, int]) -> List[int]:
    vec_size = len(trigrams.keys())
    max_count = max(trigrams.values())

    assert max_count + 1 == vec_size, "Maximum index should be one less than vector size"
    raw_vector = [0] * vec_size  # initialize vector

    for i in range(len(processed_text) - 2):
        trigram = processed_text[i: i + 3]
        if trigrams.get(trigram) is not None:  # NOTE: explicit None check because 0 is also present
            raw_vector[trigrams[trigram]] += 1
    return raw_vector


def normalize_count_vector(count_vector: List[int]) -> List[float]:
    total_count = sum(count_vector)
    return [round(x / total_count, 5) for x in count_vector]


def create_trigram_vector(lang: str, text: str) -> List[float]:
    trigrams = None
    if lang not in SUPPORTED_LANGUAGES:
        raise InvalidLanguage(f'Invalid lanaguage "{lang}" to process trigrams')

    if lang == 'en':
        trigrams = EN_TRIGRAMS
    elif lang == 'es':
        trigrams = ES_TRIGRAMS
    elif lang == 'fr':
        trigrams = FR_TRIGRAMS

    if not trigrams:
        raise TrigramsNotLoaded(f'Trigrams for language "{lang}" are not loaded.')

    if text is None:
        raise InvalidText('No document')

    punc_removed = remove_puncs_and_extra_spaces(text)
    if len(punc_removed) < 3:
        raise InvalidText('Too small document')
    count_vector = create_count_vector(punc_removed, trigrams)
    return normalize_count_vector(count_vector)
