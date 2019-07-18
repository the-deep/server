from django.db import models
from django.contrib.postgres.fields import JSONField
from user_resource.models import UserResource
from user.models import User


class AnalysisFramework(UserResource):
    """
    Analysis framework defining framework to do analysis

    Analysis is done to create entries out of leads.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    is_private = models.BooleanField(default=False)

    members = models.ManyToManyField(
        User, blank=True,
        through_fields=('framework', 'member'),
        through='AnalysisFrameworkMembership'
    )

    def __str__(self):
        return self.title

    def clone(self, user, overrides={}):
        """
        Clone analysis framework along with all widgets,
        filters and exportables
        """
        title = overrides.get('title', '{} (cloned)'.format(
            self.title[:230]))  # Strip off extra chars from title
        description = overrides.get('description', '')
        analysis_framework = AnalysisFramework(
            title=title,
            description=description,
        )
        analysis_framework.created_by = user
        analysis_framework.modified_by = user
        analysis_framework.save()

        [widget.clone_to(analysis_framework) for widget
         in self.widget_set.all()]

        return analysis_framework

    @staticmethod
    def get_for(user):
        return AnalysisFramework.objects.all().exclude(
            models.Q(is_private=True) & ~models.Q(members=user)
        )

    def can_get(self, user):
        return True

    def can_modify(self, user):
        """
        Analysis framework can be modified by a user if:
        * user created the framework, or
        * user is super user, or
        * the framework belongs to a project where the user is admin
        """
        return (
            self.created_by == user or
            user.is_superuser or
            AnalysisFrameworkMembership.objects.filter(
                member=user,
                framework=self,
                role__can_edit_framework=True
            ).exists()
        )

    def can_clone(self, user):
        return (
            not self.is_private or
            AnalysisFrameworkMembership.objects.filter(
                member=user,
                framework=self,
                role__can_clone_framework=True,
            ).exists()
        )

    def get_entries_count(self):
        from entry.models import Entry
        return Entry.objects.filter(analysis_framework=self).count()

    def get_or_create_owner_role(self):
        permission_fields = self.get_owner_permissions()
        privacy_label = 'Private' if self.is_private else 'Public'
        role, created = AnalysisFrameworkRole.objects.get_or_create(
            **permission_fields,
            is_private_role=self.is_private,
            defaults={
                'title': f'Owner Role({privacy_label})'
            }
        )
        return role

    def get_or_create_editor_role(self):
        permission_fields = self.get_editor_permissions()
        privacy_label = 'Private' if self.is_private else 'Public'

        role, created = AnalysisFrameworkRole.objects.get_or_create(
            **permission_fields,
            is_private_role=self.is_private,
            defaults={
                'title': f'Editor Role({privacy_label})'
            }
        )
        return role

    def get_or_create_default_role(self):
        permission_fields = self.get_default_permissions()
        privacy_label = 'Private' if self.is_private else 'Public'
        role, created = AnalysisFrameworkRole.objects.get_or_create(
            is_default_role=True,
            is_private_role=self.is_private,
            defaults={
                **permission_fields,
                'title': f'Default({privacy_label})',
            }
        )
        return role

    def add_member(self, user, role=None, added_by=None):
        role = role or self.get_or_create_default_role()
        return AnalysisFrameworkMembership.objects.get_or_create(
            member=user,
            framework=self,
            role=role,
            defaults={
                'added_by': added_by,
            },
        )

    def get_default_permissions(self):
        # For now, same for both private and public, change later if needed
        AFRole = AnalysisFrameworkRole
        permission_fields = {x: False for x in AFRole.PERMISSION_FIELDS}
        permission_fields[AFRole.CAN_USE_IN_OTHER_PROJECTS] = True
        return permission_fields

    def get_editor_permissions(self):
        AFRole = AnalysisFrameworkRole
        permission_fields = {x: True for x in AFRole.PERMISSION_FIELDS}
        permission_fields[AFRole.CAN_ADD_USER] = False

        if self.is_private:
            permission_fields[AFRole.CAN_CLONE_FRAMEWORK] = False

        return permission_fields

    def get_owner_permissions(self):
        AFRole = AnalysisFrameworkRole
        permission_fields = {x: True for x in AFRole.PERMISSION_FIELDS}
        permission_fields[AFRole.CAN_CLONE_FRAMEWORK] = False

        if not self.is_private:
            permission_fields[AFRole.CAN_CLONE_FRAMEWORK] = True
        return permission_fields


class Widget(models.Model):
    """
    Widget inserted into a framework
    """
    analysis_framework = models.ForeignKey(
        AnalysisFramework, on_delete=models.CASCADE,
    )
    key = models.CharField(max_length=100, default=None, blank=True, null=True)
    widget_id = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    properties = JSONField(default=None, blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .utils import update_widget
        update_widget(self)

    def __str__(self):
        return '{} ({})'.format(self.title, self.widget_id)

    def clone_to(self, analysis_framework):
        widget = Widget(
            analysis_framework=analysis_framework,
            key=self.key,
            widget_id=self.widget_id,
            title=self.title,
            properties=self.properties,
        )
        widget.save()
        return widget

    @staticmethod
    def get_for(user):
        """
        Widget can only be accessed by users who have access to
        AnalysisFramework which has access to it's project
        """
        return Widget.objects.filter(
            models.Q(analysis_framework__project=None) |
            models.Q(analysis_framework__project__members=user) |
            models.Q(analysis_framework__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.analysis_framework.can_get(user)

    def can_modify(self, user):
        return self.analysis_framework.can_modify(user)


class Filter(models.Model):
    """
    A filter for a widget in an analysis framework
    """
    NUMBER = 'number'
    LIST = 'list'
    INTERSECTS = 'intersects'

    FILTER_TYPES = (
        (NUMBER, 'Number'),
        (LIST, 'List'),
        (INTERSECTS, 'Intersection between two numbers'),
    )

    analysis_framework = models.ForeignKey(
        AnalysisFramework, on_delete=models.CASCADE,
    )
    key = models.CharField(max_length=100, db_index=True)
    widget_key = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    properties = JSONField(default=None, blank=True, null=True)
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPES,
                                   default=LIST)

    class Meta:
        ordering = ['title', 'widget_key', 'key']

    def __str__(self):
        return '{} ({})'.format(self.title, self.key)

    def clone_to(self, analysis_framework):
        filter = Filter(
            analysis_framework=analysis_framework,
            key=self.key,
            widget_key=self.widget_key,
            title=self.title,
            properties=self.properties,
            filter_type=self.filter_type,
        )
        filter.save()
        return filter

    @staticmethod
    def get_for(user):
        """
        Filter can only be accessed by users who have access to
        AnalysisFramework which has access to it's project
        """
        return Filter.objects.filter(
            models.Q(analysis_framework__project=None) |
            models.Q(analysis_framework__project__members=user) |
            models.Q(analysis_framework__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.analysis_framework.can_get(user)

    def can_modify(self, user):
        return self.analysis_framework.can_modify(user)


class Exportable(models.Model):
    """
    Export data for given widget
    """
    analysis_framework = models.ForeignKey(
        AnalysisFramework, on_delete=models.CASCADE,
    )
    widget_key = models.CharField(max_length=100, db_index=True)
    inline = models.BooleanField(default=False)
    order = models.IntegerField(default=1)
    data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return 'Exportable ({})'.format(self.widget_key)

    class Meta:
        ordering = ['order']

    def clone_to(self, analysis_framework):
        exportable = Exportable(
            analysis_framework=analysis_framework,
            widget_key=self.widget_key,
            inline=self.inline,
        )
        exportable.save()
        return exportable

    @staticmethod
    def get_for(user):
        """
        Exportable can only be accessed by users who have access to
        AnalysisFramework which has access to it's project
        """
        return Exportable.objects.filter(
            models.Q(analysis_framework__project=None) |
            models.Q(analysis_framework__project__members=user) |
            models.Q(analysis_framework__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.analysis_framework.can_get(user)

    def can_modify(self, user):
        return self.analysis_framework.can_modify(user)


class AnalysisFrameworkRole(models.Model):
    """
    Roles for AnalysisFramework
    """
    CAN_ADD_USER = 'can_add_user'
    CAN_CLONE_FRAMEWORK = 'can_clone_framework'
    CAN_EDIT_FRAMEWORK = 'can_edit_framework'
    CAN_USE_IN_OTHER_PROJECTS = 'can_use_in_other_projects'

    PERMISSION_FIELDS = (
        CAN_ADD_USER,
        CAN_CLONE_FRAMEWORK,
        CAN_EDIT_FRAMEWORK,
        CAN_USE_IN_OTHER_PROJECTS,
    )

    title = models.CharField(max_length=255, unique=True)
    is_private_role = models.BooleanField(default=False)

    # The following field allows user to add other users to the framework and
    # assign appropriate permissions
    can_add_user = models.BooleanField(default=False)

    can_clone_framework = models.BooleanField(default=False)

    can_edit_framework = models.BooleanField(default=False)

    can_use_in_other_projects = models.BooleanField(default=False)

    is_default_role = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            'can_add_user',
            'can_clone_framework',
            'can_edit_framework',
            'is_private_role',
            'can_use_in_other_projects',
            'is_default_role'
        )

    def __str__(self):
        return self.title

    @property
    def permissions(self):
        return {
            x: self.__dict__[x]
            for x in AnalysisFrameworkRole.PERMISSION_FIELDS
        }


class AnalysisFrameworkMembership(models.Model):
    member = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='framework_membership'
    )
    framework = models.ForeignKey(AnalysisFramework, on_delete=models.CASCADE)
    role = models.ForeignKey(
        AnalysisFrameworkRole,
        on_delete=models.CASCADE,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        null=True, blank=True, default=None,
    )

    class Meta:
        unique_together = ('member', 'framework')

    @staticmethod
    def get_for(user):
        return AnalysisFrameworkMembership.objects.all()  # filter(
#             framework__members=user,
            # role__can_add_user=True,
#         )
