from django.contrib.postgres.fields import JSONField
from django.db import models
from user_resource.models import UserResource


class CategoryEditor(UserResource):
    title = models.CharField(max_length=255)
    data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title

    def clone(self, user):
        """
        Clone category editor
        """
        category_editor = CategoryEditor(
            title='{} (cloned)'.format(self.title),
            data=self.data,
        )
        category_editor.created_by = user
        category_editor.modified_by = user
        category_editor.save()

        return category_editor

    @staticmethod
    def get_for(user):
        """
        Category Editor can only be accessed by users who have access to
        it's project
        """
        return CategoryEditor.objects.filter(
            models.Q(project=None) |
            models.Q(project__members=user) |
            models.Q(project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self in CategoryEditor.get_for(user)

    def can_modify(self, user):
        """
        Category editor can be modified by a user if:
        * user created the it, or
        * user is super user, or
        * it belongs to a project where the user is admin
        """
        import project
        return (
            self.created_by == user or
            user.is_superuser or
            project.models.ProjectMembership.objects.filter(
                project__in=self.project_set.all(),
                member=user,
                role='admin',
            ).exists()
        )
