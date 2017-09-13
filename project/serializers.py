from rest_framework import serializers
from project.models import Project, ProjectMembership


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('pk', 'title', 'members', 'regions',
                  'user_groups', 'data')

    def create(self, validated_data):
        project = super(Project, self).create(validated_data)
        ProjectMembership.objects.create(
            project=project,
            member=self.context['request'].user,
            role='admin'
        )
        return project


class ProjectMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMembership
        fields = ('pk', 'member', 'project', 'role', 'joined_at')
