from category_editor.models import CategoryEditor
from drf_dynamic_fields import DynamicFieldsMixin
from project.models import Project
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer

from deep.serializers import RemoveNullFieldsMixin


class CategoryEditorSerializer(RemoveNullFieldsMixin, DynamicFieldsMixin, UserResourceSerializer):
    is_admin = serializers.SerializerMethodField()
    project = serializers.IntegerField(
        write_only=True,
        required=False,
    )
    projects = serializers.PrimaryKeyRelatedField(
        source="project_set.all",
        read_only=True,
        many=True,
    )

    class Meta:
        model = CategoryEditor
        fields = "__all__"

    def validate_project(self, project):
        try:
            project = Project.objects.get(id=project)
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project matching query does not exist")

        if not project.can_modify(self.context["request"].user):
            raise serializers.ValidationError("Invalid project")
        return project.id

    def create(self, validated_data):
        project = validated_data.pop("project", None)
        ce = super().create(validated_data)

        if project:
            project = Project.objects.get(id=project)
            project.category_editor = ce
            project.modified_by = self.context["request"].user
            project.save()

        return ce

    def get_is_admin(self, category_editor):
        return category_editor.can_modify(self.context["request"].user)
