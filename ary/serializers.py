from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer

from .models import (
    AssessmentTemplate,
    Assessment,
)


class AssessmentSerializer(DynamicFieldsMixin, UserResourceSerializer):
    class Meta:
        model = Assessment
        fields = ('__all__')


class AssessmentTemplateSerializer(DynamicFieldsMixin, UserResourceSerializer):
    metadata_groups = serializers.SerializerMethodField()
    methodology_groups = serializers.SerializerMethodField()
    assessment_topics = serializers.SerializerMethodField()
    affected_groups = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentTemplate
        fields = ('__all__')

    def serialize_item(self, item):
        return {
            'id': item.id,
            'title': item.title,
        }

    def serialize_field(self, field):
        return {
            'id': field.id,
            'title': field.title,
            'field_type': field.field_type,
            'options': [
                self.serialize_item(option)
                for option in field.options.all()
            ],
        }

    def serialize_group(self, group):
        return {
            'id': group.id,
            'title': group.title,
            'fields': [
                self.serialize_field(field)
                for field in group.fields.all()
            ],
        }

    def serialize_node(self, node):
        return {
            'id': node.id,
            'title': node.title,
            'children': [
                self.serialize_node(child)
                for child in node.children.all()
            ]
        }

    def get_metadata_groups(self, template):
        return [
            self.serialize_group(group)
            for group in template.metadatagroup_set.all()
        ]

    def get_methodology_groups(self, template):
        return [
            self.serialize_group(group)
            for group in template.methodologygroup_set.all()
        ]

    def get_assessment_topics(self, template):
        return [
            self.serialize_item(topic)
            for topic in template.assessmenttopic_set.all()
        ]

    def get_affected_groups(self, template):
        parent = template.affectedgroup_set.filter(parent=None).first()
        return parent and self.serialize_node(parent)
