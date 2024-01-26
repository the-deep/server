import json
import hashlib
from typing import Union

from django.core.cache import cache, caches
from django.core.serializers.json import DjangoJSONEncoder


local_cache = caches['local-memory']


def clear_cache(prefix):
    try:
        cache.delete_many(
            cache.keys(prefix + '*')
        )
        return True
    except Exception:
        pass


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
        BASE = 'EXPLORE-DEEP-'
        _PREFIX = BASE + '{}-'
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
        TOTAL_ENTRIES_ADDED_LAST_WEEK_COUNT = BASE + 'TOTAL_ENTRIES_ADDED_LAST_WEEK_COUNT'

        @classmethod
        def clear_cache(cls):
            return clear_cache(cls.BASE)

    class Tracker:
        BASE = 'DEEP-TRACKER-'
        # Dynamic
        LAST_PROJECT_READ_ACCESS_DATETIME = BASE + 'LAST-PROJECT-READ-ACCESS-DATETIME-'
        LAST_PROJECT_WRITE_ACCESS_DATETIME = BASE + 'LAST-PROJECT-WRITE-ACCESS-DATETIME-'
        LAST_USER_ACTIVE_DATETIME = BASE + 'LAST-USER-ACTIVE-DATETIME-'

    class AssessmentDashboard:
        BASE = 'ASSESSMENT-DASHBOARD-'
        _PREFIX = BASE + '{}-'

        TOTAL_ASSESSMENT_COUNT = _PREFIX + 'TOTAL-ASSESSMENT'
        TOTAL_STAKEHOLDER_COUNT = _PREFIX + 'TOTAL-STAKEHOLDER'
        TOTAL_COLLECTION_TECHNIQUE_COUNT = _PREFIX + 'TOTAL-COLLECTION_TECHNIQUE'
        OVER_THE_TIME = _PREFIX + 'OVER-THE-TIME'
        ASSESSMENT_COUNT = _PREFIX + 'ASSESSMENT-COUNT'
        STAKEHOLDER_COUNT = _PREFIX + 'STAKEHOLDER-COUNT'
        TOTAL_MULTISECTOR_ASSESSMENT_COUNT = _PREFIX + 'TOTAL-MULTISECTOR-ASSESSMENT-COUNT'
        TOTAL_SINGLESECTOR_ASSESSMENT_COUNT = _PREFIX + 'TOTAL-SINGLESECTOR-ASSESSMENT-COUNT'
        COLLECTION_TECHNIQUE_COUNT = _PREFIX + 'COLLECTION-TECHNIQUE-COUNT'
        ASSESSMENT_PER_FRAMEWORK_PILLAR = _PREFIX + 'ASSESSMENT-PER-FRAMEWORK-PILLAR'
        ASSESSMENT_PER_AFFECTED_GROUP = _PREFIX + 'ASSESSMENT-PER-AFFECTED-GROUP'
        ASSESSMENT_PER_HUMANITRATION_SECTOR = _PREFIX + 'ASSESSMENT-PER-HUMANITRATION-SECTOR'
        ASSESSMENT_PER_PROTECTION_MANAGEMENT = _PREFIX + 'ASSESSMENT-PER-PROTECTION-MANAGEMENT'
        ASSESSMENT_SECTOR_AND_GEOAREA = _PREFIX + 'ASSESSMENT-SECTOR-AND-GEOAREA'
        ASSESSMENT_AFFECTED_GROUP_AND_GEOAREA = _PREFIX + 'ASSESSMENT-AFFECTED-GROUP-AND-GEOAREA'
        ASSESSMENT_AFFECTED_GROUP_AND_SECTOR = _PREFIX + 'ASSESSMENT-AFFECTED-GROUP-AND-SECTOR'
        ASSESSMENT_BY_LEAD_ORGANIZATION = _PREFIX + 'ASSESSMENT-BY-LEAD-ORGANIZATION'
        ASSESSMENT_PER_DATA_COLLECTION_TECHNIQUE = _PREFIX + 'ASSESSMENT-PER-DATA-COLLECTION-TECHNIQUE'
        ASSESSMENT_PER_UNIT_ANALYSIS = _PREFIX + 'ASSESSMENT-PER-UNIT-ANALYSIS'
        ASSESSMENT_PER_UNIT_REPORTING = _PREFIX + 'ASSESSMENT-PER-UNIT-REPORTING'
        ASSESSMENT_PER_SAMPLE_APPROACH = _PREFIX + 'ASSESSMENT-PER-SAMPLE-APPROACH'
        ASSESSMENT_PER_PROXIMITY = _PREFIX + 'ASSESSMENT-PER-PROXIMITY'
        ASSESSMENT_BY_GEOAREA = _PREFIX + 'ASSESSMENT-BY-GEOAREA'
        SAMPLE_SIZE_PER_DATA_COLLECTION_TECHNIQUE = _PREFIX + 'SAMPLE-SIZE-PER-DATA-COLLECTION-TECHNIQUE'
        DATA_COLLECTION_TECHNIQUE_AND_GEOLOCATION = _PREFIX + 'DATA-COLLECTION-TECHNIQUE-AND-GEOLOCATION'
        MEDIAN_SCORE_BY_SECTOR_AND_AFFECTED_GROUP_BY_MONTH = _PREFIX + 'MEDIAN-SCORE-BY-SECTOR-AND-AFFECTED-GROUP-BY-MONTH'
        MEDIAN_SCORE_BY_SECTOR_AND_AFFECTED_GROUP = _PREFIX + 'MEDIAN-SCORE-BY-SECTOR-AND-AFFECTED-GROUP'
        MEDIAN_QUALITY_SCORE_BY_GEOAREA_AND_SECTOR_BY_MONTH = _PREFIX + 'MEDIAN_SCORE_BY_SECTOR_AND_AFFECTED_GROUP_BY_MONTH'
        MEDIAN_QUALITY_SCORE_BY_GEOAREA_AND_AFFECTED_GROUP = _PREFIX + 'MEDIAN-QUALITY-SCORE-BY-GEOAREA-AND-AFFECTED-GROUP'
        MEDIAN_QUALITY_SCORE_BY_GEOAREA_AND_SECTOR = _PREFIX + 'MEDIAN-QUALIRY-SCORE-BY-GEOAREA-AND-SECTOR'
        MEDIAN_QUALITY_SCORE_BY_ANALYTICAL_DENSITY_DATE = _PREFIX + 'MEDIAN_QUALITY_SCORE_BY_ANALYTICAL_DENSITY_DATE_MONTH'
        MEDIAN_QUALITY_SCORE_BY_ANALYTICAL_DENSITY_DATE_MONTH = _PREFIX + 'MEDIAN-QUALIRY-SCORE-BY-ANALYTICAL-DENSITY-DATE'
        MEDIAN_QUALITY_SCORE_OF_ANALYTICAL_DENSITY = _PREFIX + 'MEDIAN-QUALITY-SCORE-OF_ANALYTICAL-DENSITY'
        MEDIAN_QUALITY_SCORE_OF_EACH_DIMENSION_BY_DATE_MONTH = _PREFIX + 'MEDIAN-QUALITY-SCORE-EACH-DIMENSION-BY-DATE-MONTH'
        MEDIAN_QUALITY_SCORE_OF_EACH_DIMENSION_BY_DATE = _PREFIX + 'MEDIAN-QUALITY-SCORE-EACH-DIMENSION-BY-DATE'
        MEDIAN_QUALITY_SCORE_OVER_TIME = _PREFIX + 'MEDIAN-QUALITY-SCORE-OVER-TIME'
        MEDIAN_QUALITY_SCORE_BY_GEO_AREA = _PREFIX + 'MEDIAN-QUALITY-SCORE-GEO-AREA'
        UNIT_REPORTING_AND_GEOLOCATION = _PREFIX + 'UNIT-REPORTING-AND-GEOLOCATION'
        UNIT_OF_ANALYSIS_AND_GEOLOCATION = _PREFIX + 'UNIT-OF-ANALYSIS-AND-GEOLOCATION'
        PROXIMITY_AND_GEOLOCATION = _PREFIX + 'PROXIMITY-AND-GEOLOCATION'
        SAMPLING_APPROACH_AND_GEOLOCATION = _PREFIX + 'SAMPLING-APPROCACH-AND-GEOLOCATION'
        MEDIAN_QUALITY_SCORE_OVER_TIME_BY_MONTH = _PREFIX + 'MEDIAN-QUALITY-SCORE-OVER-TIME-MONTH'
        MEDIAN_QUALITY_SCORE_OF_EACH_DIMENSION = _PREFIX + 'MEDIAN-QUALITY-SCORE-EACH-DIMENSION'

        @classmethod
        def clear_cache(cls):
            return clear_cache(cls.BASE)


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
        if isinstance(item, str):
            hashable = item
        elif isinstance(item, dict):
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
