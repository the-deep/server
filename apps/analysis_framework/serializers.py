from django.utils.functional import cached_property

from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers, exceptions
from drf_writable_nested.serializers import WritableNestedModelSerializer
from django.db.models import Q

from deep.serializers import RemoveNullFieldsMixin, TempClientIdMixin, IntegerIDField
from user_resource.serializers import UserResourceSerializer
from questionnaire.serializers import FrameworkQuestionSerializer
from user.models import User, Feature
from user.serializers import SimpleUserSerializer
from project.models import Project
from organization.serializers import SimpleOrganizationSerializer

from .models import (
    AnalysisFramework,
    AnalysisFrameworkRole,
    AnalysisFrameworkMembership,
    Widget, Section, Filter, Exportable,
)


class WidgetSerializer(RemoveNullFieldsMixin,
                       DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Widget Model Serializer
    """

    class Meta:
        model = Widget
        fields = ('__all__')

    # Validations
    def validate_analysis_framework(self, analysis_framework):
        if not analysis_framework.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Analysis Framework')
        return analysis_framework


class FilterSerializer(RemoveNullFieldsMixin,
                       DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Filter data Serializer
    """

    class Meta:
        model = Filter
        fields = ('__all__')

    # Validations
    def validate_analysis_framework(self, analysis_framework):
        if not analysis_framework.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Analysis Framework')
        return analysis_framework


class ExportableSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Export data Serializer
    """

    class Meta:
        model = Exportable
        fields = ('__all__')

    # Validations
    def validate_analysis_framework(self, analysis_framework):
        if not analysis_framework.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Analysis Framework')
        return analysis_framework


class SimpleWidgetSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = ('id', 'key', 'widget_id', 'title', 'properties', 'order', 'section')


class SimpleFilterSerializer(RemoveNullFieldsMixin,
                             serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = ('id', 'key', 'widget_key', 'title',
                  'properties', 'filter_type')


class SimpleExportableSerializer(RemoveNullFieldsMixin,
                                 serializers.ModelSerializer):
    class Meta:
        model = Exportable
        fields = ('id', 'widget_key', 'inline', 'order', 'data')


class AnalysisFrameworkRoleSerializer(
    RemoveNullFieldsMixin, serializers.ModelSerializer,
):
    class Meta:
        model = AnalysisFrameworkRole
        fields = ('__all__')


class AnalysisFrameworkMembershipSerializer(
    RemoveNullFieldsMixin, DynamicFieldsMixin, serializers.ModelSerializer,
):
    member_details = SimpleUserSerializer(read_only=True, source='member')
    role = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=AnalysisFrameworkRole.objects.all(),
    )
    added_by_details = SimpleUserSerializer(read_only=True, source='added_by')
    role_details = AnalysisFrameworkRoleSerializer(read_only=True, source='role')

    class Meta:
        model = AnalysisFrameworkMembership
        fields = ('__all__')

    def create(self, validated_data):
        user = self.context['request'].user
        framework = validated_data.get('framework')

        # NOTE: Default role is different for private and public framework
        # For public, two sorts of default role, one for non members and one while adding
        # member to af, which is editor role
        default_role = framework.get_or_create_default_role() if framework.is_private else\
            framework.get_or_create_editor_role()

        role = validated_data.get('role') or default_role

        if framework is None:
            raise serializers.ValidationError('Analysis Framework does not exist')

        membership = AnalysisFrameworkMembership.objects.filter(
            member=user,
            framework=framework,
        ).first()

        # If user is not a member of the private framework then return 404
        if membership is None and framework.is_private:
            raise exceptions.NotFound()
        elif membership is None:
            # Else if user is not member but is a public framework, return 403
            raise exceptions.PermissionDenied()

        # But if user is member and has no permissions, return 403
        if not membership.role.can_add_user:
            raise exceptions.PermissionDenied()

        if role.is_private_role and not framework.is_private:
            raise exceptions.PermissionDenied(
                {'message': 'Public framework cannot have private role'}
            )
        if not role.is_private_role and framework.is_private:
            raise exceptions.PermissionDenied(
                {'message': 'Private framework cannot have public role'}
            )

        validated_data['role'] = role  # Just in case role is not provided, add default role
        validated_data['added_by'] = user  # make request user to be added_by by default

        return super().create(validated_data)


class AnalysisFrameworkSerializer(RemoveNullFieldsMixin,
                                  DynamicFieldsMixin,
                                  UserResourceSerializer):
    """
    Analysis Framework Model Serializer
    """
    widgets = SimpleWidgetSerializer(source='widget_set', many=True, required=False)
    filters = SimpleFilterSerializer(source='get_active_filters', many=True, read_only=True)
    exportables = SimpleExportableSerializer(source='exportable_set', many=True, read_only=True)
    questions = FrameworkQuestionSerializer(source='frameworkquestion_set', many=True, required=False, read_only=True)
    entries_count = serializers.IntegerField(
        source='get_entries_count',
        read_only=True,
    )

    is_admin = serializers.SerializerMethodField()
    users_with_add_permission = serializers.SerializerMethodField()
    visible_projects = serializers.SerializerMethodField()
    all_projects_count = serializers.IntegerField(source='project_set.count', read_only=True)

    project = serializers.IntegerField(
        write_only=True,
        required=False,
    )

    role = serializers.SerializerMethodField()
    organization_details = SimpleOrganizationSerializer(source='organization', read_only=True)

    class Meta:
        model = AnalysisFramework
        fields = ('__all__')

    def get_visible_projects(self, obj):
        from project.serializers import SimpleProjectSerializer
        user = None
        if 'request' in self.context:
            user = self.context['request'].user
        projects = obj.project_set.exclude(Q(is_private=True) & ~Q(members=user))
        return SimpleProjectSerializer(projects, context=self.context, many=True, read_only=True).data

    def get_users_with_add_permission(self, obj):
        """
        AF members with access to add other users to AF
        """
        return SimpleUserSerializer(
            User.objects.filter(
                id__in=obj.analysisframeworkmembership_set.filter(role__can_add_user=True).values('member'),
            ).all(),
            context=self.context,
            many=True,
        ).data

    def get_role(self, obj):
        user = self.context['request'].user
        membership = AnalysisFrameworkMembership.objects.filter(
            framework=obj,
            member=user
        ).first()

        role = None
        if not membership and not obj.is_private:
            role = obj.get_or_create_default_role()
        elif membership:
            role = membership.role
        else:
            return {}

        return AnalysisFrameworkRoleSerializer(role, context=self.context).data

    def validate_project(self, project):
        try:
            project = Project.objects.get(id=project)
        except Project.DoesNotExist:
            raise serializers.ValidationError(
                'Project matching query does not exist'
            )

        if not project.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid project')
        return project.id

    def create(self, validated_data):
        project = validated_data.pop('project', None)
        private = validated_data.get('is_private', False)

        # Check if user has access to private project feature
        user = self.context['request'].user
        private_access = user.profile.get_accessible_features().filter(
            key=Feature.FeatureKey.PRIVATE_PROJECT
        ).exists()

        if private and not private_access:
            raise exceptions.PermissionDenied({
                "message": "You don't have permission to create private framework"
            })

        af = super().create(validated_data)

        if project:
            project = Project.objects.get(id=project)
            project.analysis_framework = af
            project.modified_by = user
            project.save()

        owner_role = af.get_or_create_owner_role()
        af.add_member(self.context['request'].user, owner_role)
        return af

    def update(self, instance, validated_data):
        if 'is_private' not in validated_data:
            return super().update(instance, validated_data)

        if instance.is_private != validated_data['is_private']:
            raise exceptions.PermissionDenied({
                "message": "You don't have permission to change framework's privacy"
            })
        return super().update(instance, validated_data)

    def get_is_admin(self, analysis_framework):
        return analysis_framework.can_modify(self.context['request'].user)


# ------------------ Graphql seriazliers -----------------------------------
def validate_items_limit(items, limit, error_message='Only %d items are allowed. Provided: %d'):
    if items:
        count = len(items)
        if count > limit:
            raise serializers.ValidationError(error_message % (limit, count))


class AfWidgetLimit():
    MAX_SECTIONS_ALLOWED = 5
    MAX_WIDGETS_ALLOWED_PER_SECTION = 10
    MAX_WIDGETS_ALLOWED_IN_SECONDARY_TAGGING = 50


class WidgetGqlSerializer(TempClientIdMixin, serializers.ModelSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = Widget
        fields = (
            'id', 'key', 'widget_id', 'title', 'properties', 'order', 'width',
            'client_id',
        )


# TODO: Using WritableNestedModelSerializer here, let's use this everywhere instead of using custom serializer.
class SectionGqlSerializer(TempClientIdMixin, WritableNestedModelSerializer):
    id = IntegerIDField(required=False)
    widgets = WidgetGqlSerializer(source='widget_set', many=True, required=False)

    class Meta:
        model = Section
        fields = (
            'id', 'title', 'order', 'tooltip',
            'widgets',
            'client_id',
        )

    # NOTE: This is a custom function (apps/user_resource/serializers.py::UserResourceSerializer)
    # This makes sure only scoped (individual AF) instances (widgets) are updated.
    # TODO: Check this
    def _get_prefetch_related_instances_qs(self, qs):
        if self.instance:
            return qs.filter(analysis_framework=self.instance.analysis_framework_id)
        return qs.none()  # On create throw error if existing id is provided

    def validate_widgets(self, items):
        # Check max limit for widgets
        validate_items_limit(items, AfWidgetLimit.MAX_WIDGETS_ALLOWED_PER_SECTION)
        return items


class AnalysisFrameworkGqlSerializer(UserResourceSerializer):
    primary_tagging = SectionGqlSerializer(source='section_set', many=True, required=False)
    secondary_tagging = WidgetGqlSerializer(many=True, write_only=False, required=False)
    client_id = None  # Inherited from UserResourceSerializer

    class Meta:
        model = AnalysisFramework
        fields = (
            'title', 'description', 'is_private', 'properties', 'organization', 'preview_image',
            'created_at', 'created_by', 'modified_at', 'modified_by',
            'primary_tagging', 'secondary_tagging',
        )

    # NOTE: This is a custom function (apps/user_resource/serializers.py::UserResourceSerializer)
    # This makes sure only scoped (individual AF) instances (widgets) are updated.
    # For Secondary tagging
    def _get_prefetch_related_instances_qs(self, qs):
        if self.instance:
            return qs.filter(analysis_framework=self.instance)
        return qs.none()  # On create throw error if existing id is provided

    def validate_is_private(self, value):
        # Changing AF Privacy is not allowed (Existing AF)
        if self.instance:
            if self.instance.is_private != value:
                raise exceptions.PermissionDenied({
                    "is_private": "You don't have permission to change framework's privacy"
                })
            return value
        # Requires feature access for Private project (New AF)
        if value and not self.context['request'].user.have_feature_access(Feature.FeatureKey.PRIVATE_PROJECT):
            raise exceptions.PermissionDenied({
                "is_private": "You don't have permission to create/update private framework"
            })
        return value

    def validate_primary_tagging(self, items):
        # Check max limit for sections
        validate_items_limit(items, AfWidgetLimit.MAX_SECTIONS_ALLOWED)
        return items

    def validate_secondary_tagging(self, items):
        # Check max limit for secondary_tagging
        validate_items_limit(items, AfWidgetLimit.MAX_WIDGETS_ALLOWED_IN_SECONDARY_TAGGING)
        return items

    def _delete_old_secondary_taggings(self, af, secondary_tagging):
        current_ids = [
            widget_data['id'] for widget_data in secondary_tagging
            if 'id' in widget_data
        ]
        qs_to_delete = Widget.objects\
            .filter(
                analysis_framework=af,
                section__isnull=True,  # NOTE: section are null for secondary taggings
            ).exclude(pk__in=current_ids)  # Exclude current provided widgets
        qs_to_delete.delete()

    def _save_secondary_taggings(self, af, secondary_tagging):
        # Create secondary tagging widgets (Primary/Section widgets are created using WritableNestedModelSerializer)
        for widget_data in secondary_tagging:
            id = widget_data.get('id')
            widget = None
            if id:
                widget = Widget.objects.filter(analysis_framework=af, pk=id).first()
            serializer = WidgetGqlSerializer(
                instance=widget,
                data=widget_data,
                context=self.context,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)  # This might be already validated
            serializer.save(analysis_framework=af)

    def create(self, validated_data):
        secondary_tagging = validated_data.pop('secondary_tagging', None)
        # Create AF
        instance = super().create(validated_data)
        secondary_tagging and self._save_secondary_taggings(instance, secondary_tagging)
        # Create a owner role
        owner_role = instance.get_or_create_owner_role()
        instance.add_member(self.context['request'].user, owner_role)
        # NOTE: Set current_user_role value. (get_current_user_role)
        instance.current_user_role = owner_role.title
        return instance

    def update(self, instance, validated_data):
        secondary_tagging = validated_data.pop('secondary_tagging', None)
        # Update AF
        instance = super().update(instance, validated_data)
        # Update secondary_tagging
        if secondary_tagging is not None:
            self._delete_old_secondary_taggings(instance, secondary_tagging)
            self._save_secondary_taggings(instance, secondary_tagging)
        # Create a owner role for created_by if it's removed
        if instance.created_by_id and not instance.members.filter(id=instance.created_by_id).exists():
            owner_role = instance.get_or_create_owner_role()
            instance.add_member(instance.created_by, owner_role)
        return instance


class AnalysisFrameworkMembershipGqlSerializer(TempClientIdMixin, serializers.ModelSerializer):
    id = IntegerIDField(required=False)
    role = serializers.PrimaryKeyRelatedField(required=False, queryset=AnalysisFrameworkRole.objects.all())

    class Meta:
        model = AnalysisFrameworkMembership
        fields = (
            'id', 'member', 'role',
            'client_id'
        )

    @cached_property
    def framework(self):
        framework = self.context['request'].active_af
        # This is a rare case, just to make sure this is validated
        if self.instance and self.instance.framework != framework:
            raise serializers.ValidationError('Invalid access')
        return framework

    def _get_default_role(self):
        # NOTE: Default role is different for private and public framework
        # For public, two sorts of default role, one for non members and one while adding
        # member to af, which is editor role
        default_role = self.framework.get_or_create_editor_role()
        if self.framework.is_private:
            default_role = self.framework.get_or_create_default_role()
        return default_role

    def validate_member(self, member):
        current_members = AnalysisFrameworkMembership.objects.filter(framework=self.framework, member=member)
        if current_members.exclude(pk=self.instance and self.instance.pk).exists():
            raise serializers.ValidationError('User is already a member!')
        return member

    def validate_role(self, role):
        if role.is_private_role and not self.framework.is_private:
            raise serializers.ValidationError('Public framework cannot have private role')
        if not role.is_private_role and self.framework.is_private:
            raise serializers.ValidationError('Private framework cannot have public role')
        return role

    def create(self, validated_data):
        # use default role if not provided on creation.
        validated_data['role'] = validated_data.get('role', self._get_default_role())
        # make request user to be added_by by default
        validated_data['framework'] = self.framework
        validated_data['added_by'] = self.context['request'].user
        return super().create(validated_data)
