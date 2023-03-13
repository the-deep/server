import json
import hashlib
from typing import Union

from django.core.cache import cache, caches
from django.core.serializers.json import DjangoJSONEncoder


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
        _PREFIX_STATIC = 'EXPLORE-DEEP-'
        # Dynamic
        TOTAL_PROJECTS_COUNT = _PREFIX + 'TOTAL-PROJECTS'
        TOTAL_REGISTERED_USERS_COUNT = _PREFIX + 'TOTAL-REGISTERED-USERS'
        TOTAL_LEADS_COUNT = _PREFIX + 'TOTAL-LEADS'
        TOTAL_ENTRIES_COUNT = _PREFIX + 'TOTAL-ENTRIES'
        TOTAL_ACTIVE_USERS_COUNT = _PREFIX + 'TOTAL-ACTIVE-USERS'
        TOTAL_AUTHORS_COUNT = _PREFIX + 'TOTAL-AUTHORS'
        TOTAL_PUBLISHERS_COUNT = _PREFIX + 'TOTAL-PUBLISHERS'
        TOP_TEN_AUTHORS_LIST = _PREFIX + 'TOP-TEN-AUTHORS'
        TOP_TEN_PUBLISHERS_LIST = _PREFIX + 'TOP-TEN-PUBLISHERS'
        TOP_TEN_FRAMEWORKS_LIST = _PREFIX + 'TOP-TEN-FRAMEWORKS'
        TOP_TEN_PROJECTS_BY_USERS_LIST = _PREFIX + 'TOP-TEN-PROJECTS-BY-USERS'
        TOP_TEN_PROJECTS_BY_ENTRIES_LIST = _PREFIX + 'TOP-TEN-PROJECTS-BY-ENTRIES'
        TOP_TEN_PROJECTS_BY_SOURCES_LIST = _PREFIX + 'TOP-TEN-PROJECTS-BY-SOURCES'
        # Static
        TOTAL_ENTRIES_ADDED_LAST_WEEK_COUNT = _PREFIX_STATIC + 'TOTAL_ENTRIES_ADDED_LAST_WEEK_COUNT'


class CacheHelper:
    @staticmethod
    def calculate_md5_str(string):
        hash_md5 = hashlib.md5()
        hash_md5.update(string)
        return hash_md5.hexdigest()

    @classmethod
    def generate_hash(cls, item: Union[None, str, dict]) -> str:
        if item is None:
            return ''
        hashable = None
        if type(item) == str:
            hashable = item
        elif type(item) == dict:
            hashable = json.dumps(
                item,
                sort_keys=True,
                indent=2,
                cls=DjangoJSONEncoder,
            ).encode('utf-8')
        else:
            raise Exception(f'Unknown Type: {type(item)}')
        return cls.calculate_md5_str(hashable)

    @staticmethod
    def gql_cache(cache_key, cache_key_gen=None, timeout=60):
        def _dec(func):
            def _caller(*args, **kwargs):
                if cache_key_gen:
                    _cache_key = cache_key.format(
                        cache_key_gen(*args, **kwargs)
                    )
                else:
                    _cache_key = cache_key
                return cache.get_or_set(
                    _cache_key,
                    lambda: func(*args, **kwargs),
                    timeout,
                )
            _caller.__name__ = func.__name__
            _caller.__module__ = func.__module__
            return _caller
        return _dec
