from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer

from .models import (
    AssessmentTemplate,

    MetadataGroup,
    MetadataField,
    MetadataOption,

    MethodologyGroup,
    MethodologyField,
    MethodologyOption,

    AssessmentTopic,
    AffectedGroup,

    Assessment,
)

