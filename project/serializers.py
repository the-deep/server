from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from project.models import Project, ProjectMembership


class ProjectSerializer(UserResourceSerializer):
    memberships = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('pk', 'title', 'members', 'regions',
                  'memberships',
                  'user_groups', 'data',
                  'created_at', 'created_by', 'modified_at', 'modified_by')

    def create(self, validated_data):
        project = super(ProjectSerializer, self).create(validated_data)
        ProjectMembership.objects.create(
            project=project,
            member=self.context['request'].user,
            role='admin'
        )
        return project

    def get_memberships(self, project):
        return ProjectMembership.objects.filter(project=project)\
            .distinct().values_list('id', flat=True)


class ProjectMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMembership
        fields = ('pk', 'member', 'project', 'role', 'joined_at')
