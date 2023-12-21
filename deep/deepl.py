from django.conf import settings


DEEPL_SERVICE_DOMAIN = settings.DEEPL_SERVICE_DOMAIN
DEEPL_SERVER_DOMAIN = settings.DEEPL_SERVER_DOMAIN


class DeeplServiceEndpoint():
    # DEEPL Service Endpoints (Existing/Legacy)
    # NOTE: This will be moved to server endpoints in near future
    ASSISTED_TAGGING_MODELS_ENDPOINT = f'{DEEPL_SERVICE_DOMAIN}/model_info'

    # DEEPL Server Endpoints (New)
    ASSISTED_TAGGING_TAGS_ENDPOINT = f'{DEEPL_SERVER_DOMAIN}/api/v1/nlp-tags/'
    DOCS_EXTRACTOR_ENDPOINT = f'{DEEPL_SERVER_DOMAIN}/api/v1/text-extraction/'
    ANALYSIS_TOPIC_MODEL = f'{DEEPL_SERVER_DOMAIN}/api/v1/topicmodel/'
    ANALYSIS_AUTOMATIC_SUMMARY = f'{DEEPL_SERVER_DOMAIN}/api/v1/summarization/'
    ANALYSIS_AUTOMATIC_NGRAM = f'{DEEPL_SERVER_DOMAIN}/api/v1/ngrams/'
    ANALYSIS_GEO = f'{DEEPL_SERVER_DOMAIN}/api/v1/geolocation/'
    ASSISTED_TAGGING_ENTRY_PREDICT_ENDPOINT = f'{DEEPL_SERVER_DOMAIN}/api/v1/entry-classification/'
    ENTRY_EXTRACTION_CLASSIFICATION = f'{DEEPL_SERVER_DOMAIN}/api/v1/entry-extraction-classification/'
