from assessment_registry.models import MethodologyAttribute

default_values = {}


def format_value(val):
    if isinstance(val, list):
        return ",".join(val)
    if val is None:
        val = ""
    return str(val)


def get_data_collection_techniques_info(assessment):
    attributes = MethodologyAttribute.objects.filter(assessment_registry=assessment)
    data = [
        {
            "Data Collection Technique": attr.get_data_collection_technique_display(),
            "Sampling Size": attr.get_sampling_approach_display(),
            "Sampling Approach": attr.sampling_size,
            "Proximity": attr.get_proximity_display(),
            "Unit of Analysis": attr.get_unit_of_analysis_display(),
            "Unit of reporting": attr.get_unit_of_reporting_display(),
        }
        for attr in attributes
    ]
    return {
        "data_collection_technique": data,
    }
