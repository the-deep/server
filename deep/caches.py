from django.core.cache import caches


local_cache = caches['local-memory']


class CacheKey:
    # Redis Cache
    URL_CACHED_FILE_FIELD_KEY_FORMAT = 'url_cache_{}'
    CONNECTOR_KEY_FORMAT = 'connector_{}'
    EXPORT_TASK_CACHE_KEY_FORMAT = 'EXPORT-{}-TASK-ID'
    GENERIC_EXPORT_TASK_CACHE_KEY_FORMAT = 'GENERIC-EXPORT-{}-TASK-ID'
    PROJECT_EXPLORE_STATS_LOADER_KEY = 'project-explore-stats-loader'
    RECENT_ACTIVITIES_KEY_FORMAT = 'user-recent-activities-{}'

    # Local (RAM) Cache
    TEMP_CLIENT_ID_KEY_FORMAT = 'client-id-mixin-{request_hash}-{instance_type}-{instance_id}'
    TEMP_CUSTOM_CLIENT_ID_KEY_FORMAT = '{prefix}-client-id-mixin-{request_hash}-{instance_type}-{instance_id}'

    class ExploreDeep:
        _PREFIX = 'EXPLORE-DEEP-{}-'
        TOTAL_PROJECTS = _PREFIX + 'TOTAL-PROJECTS'
        TOTAL_REGISTERED_USERS = _PREFIX + 'TOTAL-REGISTERED-USERS'
        TOTAL_LEADS = _PREFIX + 'TOTAL-LEADS'
        TOTAL_ENTRIES = _PREFIX + 'TOTAL-ENTRIES'
        TOTAL_ACTIVE_USERS = _PREFIX + 'TOTAL-ACTIVE-USERS'
        TOTAL_AUTHORS = _PREFIX + 'TOTAL-AUTHORS'
        TOTAL_PUBLISHERS = _PREFIX + 'TOTAL-PUBLISHERS'
        TOP_TEN_AUTHORS = _PREFIX + 'TOP-TEN-AUTHORS'
