from user_group.enums import enum_map as user_group_enum_map
from project.enums import enum_map as project_enum_map
from analysis_framework.enums import enum_map as analysis_framework_enum_map
from lead.enums import enum_map as lead_enum_map
from entry.enums import enum_map as entry_enum_map
from export.enums import enum_map as export_enum_map
from quality_assurance.enums import enum_map as quality_assurance_enum_map

ENUM_TO_GRAPHENE_ENUM_MAP = {
    **user_group_enum_map,
    **project_enum_map,
    **analysis_framework_enum_map,
    **lead_enum_map,
    **entry_enum_map,
    **export_enum_map,
    **quality_assurance_enum_map
}
