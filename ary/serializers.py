from django.shortcuts import get_object_or_404
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from user_resource.serializers import UserResourceSerializer
from lead.models import Lead
from .models import (
    AssessmentTemplate,
    Assessment,
)


class AssessmentSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, UserResourceSerializer):
    lead_title = serializers.CharField(source='lead.title',
                                       read_only=True)

    class Meta:
        model = Assessment
        fields = ('__all__')


class LeadAssessmentSerializer(RemoveNullFieldsMixin,
                               DynamicFieldsMixin, UserResourceSerializer):
    lead_title = serializers.CharField(source='lead.title',
                                       read_only=True)

    class Meta:
        model = Assessment
        fields = ('__all__')
        read_only_fields = ('lead',)

    def create(self, validated_data):
        # If this assessment is being created for the first time,
        # we want to set lead to the one which has its id in the url
        assessment = super(LeadAssessmentSerializer, self).create({
            **validated_data,
            'lead': get_object_or_404(Lead, pk=self.initial_data['lead']),
        })
        assessment.save()
        return assessment


class AssessmentTemplateSerializer(RemoveNullFieldsMixin,
                                   DynamicFieldsMixin, UserResourceSerializer):
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

    def serialize_option(self, item):
        return {
            'key': item.key,
            'label': item.title,
        }

    def serialize_field(self, field):
        return {
            'id': field.id,
            'title': field.title,
            'field_type': field.field_type,
            'options': [
                self.serialize_option(option)
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
        return [
            self.serialize_node(parent)
            for parent in template.affectedgroup_set.filter(parent=None)
        ]
