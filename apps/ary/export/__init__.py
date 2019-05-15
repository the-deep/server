from .common import get_assessment_meta
from .stakeholders_info import get_stakeholders_info  # noqa:F401
from .summary import get_assessment_export_summary  # noqa:F401
from .locations_info import get_locations_info  # noqa:F401
from .data_collection_techniques_info import get_data_collection_techniques_info  # noqa:F401
from .affected_groups_info import get_affected_groups_info  # noqa:F401
from .scoring import get_scoring  # noqa:F401


def get_export_data(assessment):
    meta_data = get_assessment_meta(assessment)
    return {
        'summary': {
            **meta_data,
            **get_assessment_export_summary(assessment),
        },
        'stakeholders': {
            **meta_data,
            **get_stakeholders_info(assessment),
        },
        'scoring': {
            **meta_data,
            **get_scoring(assessment),
        }
    }
