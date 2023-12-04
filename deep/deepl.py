from django.conf import settings


DEEPL_SERVICE_DOMAIN = settings.DEEPL_SERVICE_DOMAIN
DEEPL_SERVER_DOMAIN = settings.DEEPL_SERVER_DOMAIN


class DeeplServiceEndpoint():
    # DEEPL Service Endpoints (Existing/Legacy)
    # NOTE: This will be moved to server endpoints in near future
    ASSISTED_TAGGING_TAGS_ENDPOINT = f'{DEEPL_SERVER_DOMAIN}/api/v1/nlp-tags/'
    ASSISTED_TAGGING_MODELS_ENDPOINT = f'{DEEPL_SERVER_DOMAIN}/model_info'
    ASSISTED_TAGGING_ENTRY_PREDICT_ENDPOINT = f'{DEEPL_SERVICE_DOMAIN}/api/v1/entry-classification/'

    # DEEPL Server Endpoints (New)
    DOCS_EXTRACTOR_ENDPOINT = f'{DEEPL_SERVER_DOMAIN}/api/v1/text-extraction/'
    ANALYSIS_TOPIC_MODEL = f'{DEEPL_SERVER_DOMAIN}/api/v1/topicmodel/'
    ANALYSIS_AUTOMATIC_SUMMARY = f'{DEEPL_SERVER_DOMAIN}/api/v1/summarization/'
    ANALYSIS_AUTOMATIC_NGRAM = f'{DEEPL_SERVER_DOMAIN}/api/v1/ngrams/'
    ANALYSIS_GEO = f'{DEEPL_SERVER_DOMAIN}/api/v1/geolocation/'

    # AutoExtraction DeepL endpoint
    ENTRY_EXTRACTION_CLASSIFICATION = f'{DEEPL_SERVER_DOMAIN}/api/v1/entry-extraction-classification/'
