from django.core.cache import caches


local_cache = caches['local-memory']


class CacheKey:
    # Redis Cache
    URL_CACHED_FILE_FIELD_KEY_FORMAT = 'url_cache_{}'
    CONNECTOR_KEY_FORMAT = 'connector_{}'
    EXPORT_TASK_CACHE_KEY_FORMAT = 'EXPORT-{}-TASK-ID'
    PROJECT_EXPLORE_STATS_LOADER_KEY = 'project-explore-stats-loader'
    RECENT_ACTIVITIES_KEY_FORMAT = 'user-recent-activities-{}'

    # Local (RAM) Cache
    TEMP_CLIENT_ID_KEY_FORMAT = 'client-id-mixin-{request_hash}-{instance_type}-{instance_id}'
    TEMP_CUSTOM_CLIENT_ID_KEY_FORMAT = '{prefix}-client-id-mixin-{request_hash}-{instance_type}-{instance_id}'
