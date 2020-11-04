import string
import json
import langdetect
from tqdm import tqdm

from lead.models import LeadPreview

# Translate punctuations to spaces
PUNC_TRANS_TABLE = str.maketrans({x: ' ' for x in string.punctuation})

ENGLISH = 'en'
FRENCH = 'fr'
SPANISH = 'es'

DOCUMENT_STATS: dict = {
    ENGLISH: dict(count=0, corpus_length=0),
    FRENCH: dict(count=0, corpus_length=0),
    SPANISH: dict(count=0, corpus_length=0),
}

TRIGRAMS_COUNT: dict = {
    ENGLISH: {},
    FRENCH: {},
    SPANISH: {}
}


def remove_puncs_and_extra_spaces(text: str) -> str:
    return ' '.join(text.translate(PUNC_TRANS_TABLE).split()).lower()


def update_trigrams_count(text: str, lang: str = ENGLISH) -> None:
    for index in range(len(text) - 2):
        trigram = text[index:index + 3]
        TRIGRAMS_COUNT[lang][trigram] = TRIGRAMS_COUNT[lang].get(trigram, 0) + 1
    return


def get_total_preview_count():
    text_previews = LeadPreview.objects.all().filter(text_extract__isnull=False)
    return text_previews.count()


def generate_trigrams(json_path, limit=None):
    """
    Generates trigrams from LeadPreview Objects and writes them to a json file.
    JSON will have the following structure:
    ```
    {
        "en": { <trigram>: <trigram_count>, ... },
        "es": { <trigram>: <trigram_count>, ... },
        "fr": { <trigram>: <trigram_count>, ... }
    }
    ```
    returns: document counts and sizes dictionary
    ```
    {
        "en": { "count": <english docs count>, "corpus_length": <all_documents_byte_size> },
        "es": { "count": <spanish docs count>, "corpus_length": <all_documents_byte_size> },
        "fr": { "count": <french docs count>, "corpus_length": <all_documents_byte_size> },
    }
    ```
    """
    text_previews = LeadPreview.objects.all().filter(text_extract__isnull=False)
    if limit:
        text_previews = text_previews[:limit]
    total_count = text_previews.count()
    print(f'TOTAL previews: {total_count}')

    if json_path:
        json_file = open(json_path, 'w')

    obj_iterator = text_previews.values_list('text_extract', flat=True).iterator(chunk_size=500)
    for preview in tqdm(obj_iterator, total=total_count):
        if not preview or len(preview.strip()) == 0:
            continue
        try:
            language = langdetect.detect(preview)
        except Exception:
            continue
        if language not in [ENGLISH, FRENCH, SPANISH]:
            continue
        cleaned = remove_puncs_and_extra_spaces(preview)
        cleaned_len = len(cleaned)
        if not cleaned or cleaned_len < 3:
            continue

        # UPdate document STATS
        DOCUMENT_STATS[language]['count'] += 1
        DOCUMENT_STATS[language]['corpus_length'] += cleaned_len
        update_trigrams_count(cleaned, language)
    print(f'Now writing to {json_path}')
    if json_path:
        json.dump(TRIGRAMS_COUNT, json_file, indent=2)
    print('All Done!!!')
    print(DOCUMENT_STATS)
    return DOCUMENT_STATS


if __name__ == '__main__':
    generate_trigrams('raw_trigrams.json')
