from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from .models import Lead


class LeadSerializer(UserResourceSerializer):
    """
    Lead Model Serializer
    """
    class Meta:
        model = Lead
        fields = ('__all__')

    # validations
    def validate_project(self, project):
        # Make sure we have access to the given project
        if not project.can_get(self.context['request'].user):
            raise serializers.ValidationError(
                'Invalid project: {}'.format(project.id))
        return project

    # TODO: Probably also validate assignee to valid list of users
