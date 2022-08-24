from typing import List, Set

from rest_framework import serializers

from utils.common import remove_empty_keys_from_dict


from .models import (
    Project,
    ProjectChangeLog,
    ProjectOrganization,
)


def get_flat_dict_diff(list1: List[dict], list2: List[dict], fields: List[str]):
    def _dict_to_tuple_set(items: List[dict]) -> Set[tuple]:
        return set(
            tuple(
                item[field]
                for field in fields
            )
            for item in items
        )

    def _tuple_to_dict_list(items: Set[tuple]) -> List[dict]:
        return [
            {
                field: item[index]
                for index, field in enumerate(fields)
            }
            for item in sorted(items)
        ]

    set_list1 = _dict_to_tuple_set(list1)
    set_list2 = _dict_to_tuple_set(list2)
    return {
        'add': _tuple_to_dict_list(set_list2 - set_list1),
        'remove': _tuple_to_dict_list(set_list1 - set_list2),
    }


def get_list_diff(list1, list2):
    set_list1 = set(list1)
    set_list2 = set(list2)
    return {
        'add': sorted(list(set_list2 - set_list1)),
        'remove': sorted(list(set_list1 - set_list2)),
    }


class ProjectOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectOrganization
        fields = ('organization', 'organization_type')


class ProjectDataSerializer(serializers.ModelSerializer):
    organizations = serializers.SerializerMethodField()
    analysis_framework = serializers.IntegerField(source='analysis_framework_id')
    regions = serializers.SerializerMethodField()
    # Members
    member_users = serializers.SerializerMethodField()
    member_user_groups = serializers.SerializerMethodField()
    project_viz_config = serializers.SerializerMethodField()

    class Meta:
        model = Project
        scalar_fields = [
            'title',
            'start_date',
            'end_date',
            'description',
            'is_private',
            'is_test',
            'is_deleted',
            'deleted_at',
            # Document sharing
            'has_publicly_viewable_unprotected_leads',
            'has_publicly_viewable_restricted_leads',
            'has_publicly_viewable_confidential_leads',
        ]
        fields = (
            *scalar_fields,
            # Defined fields
            'organizations',
            'analysis_framework',
            'regions',
            'member_users',
            'member_user_groups',
            'project_viz_config',
        )

    def get_project_viz_config(self, obj):
        stat = obj.project_stats
        return {
            'public_share': stat.public_share,
            'token': stat.token,
        }

    def get_organizations(self, obj):
        return ProjectOrganizationSerializer(
            obj.projectorganization_set.order_by('organization_id', 'organization_type'),
            many=True,
        ).data

    def get_regions(self, obj):
        return list(obj.regions.order_by('id').values_list('id', flat=True))

    def get_member_users(self, obj):
        return list(obj.members.order_by('id').values_list('id', flat=True))

    def get_member_user_groups(self, obj):
        return list(obj.user_groups.order_by('id').values_list('id', flat=True))


class ProjectChangeManager():
    ACTION_MAP = {
        'details': ProjectChangeLog.Action.PROJECT_DETAILS,
        'organizations': ProjectChangeLog.Action.ORGANIZATION,
        'regions': ProjectChangeLog.Action.REGION,
        'memberships': ProjectChangeLog.Action.MEMBERSHIP,
        'framework': ProjectChangeLog.Action.FRAMEWORK,
    }

    def __init__(self, request, project_id):
        self.project_id = project_id
        self.request = request
        self.project = None

    def __enter__(self):
        self.project_data = self.get_active_project_latest_data()
        return self

    def __exit__(self, *_):
        new_project_data = self.get_active_project_latest_data()
        self.log_full_changes(
            self.project_id,
            self.project_data,
            new_project_data,
            self.request.user,
        )

    def get_active_project_latest_data(self):
        return ProjectDataSerializer(
            Project.objects.get(pk=self.project_id)
        ).data

    @staticmethod
    def _framework_change_data(new, old, updated):
        return {
            'new': new,
            'old': old,
            'updated': updated,
        }

    @staticmethod
    def _track_viz_config(viz_config, new_viz_config):
        """
        Response:
        {
            public_share: {
                old: bool,
                new: bool,
            },
            token_changed: True
        }
        """
        changes = {}
        if viz_config['public_share'] != new_viz_config['public_share']:
            changes['public_share'] = {
                'old': viz_config['public_share'],
                'new': new_viz_config['public_share'],
            }
        if viz_config['token'] != new_viz_config['token']:
            changes['token_changed'] = True
        return changes

    @classmethod
    def _track_details(cls, project_data, new_project_data):
        details_change_data = {}
        # Details change set
        for field in ProjectDataSerializer.Meta.scalar_fields:
            old_value = project_data[field]
            new_value = new_project_data[field]
            if old_value == new_value:
                continue
            details_change_data[field] = {
                'old': old_value,
                'new': new_value,
            }
        details_change_data['project_viz_config'] = cls._track_viz_config(
            project_data['project_viz_config'],
            new_project_data['project_viz_config'],
        )
        return details_change_data

    @staticmethod
    def _track_framework(project_data, new_project_data):
        framework_id = project_data['analysis_framework']
        new_framework_id = new_project_data['analysis_framework']
        if framework_id != new_framework_id:
            return {
                'new': new_framework_id,
                'old': framework_id,
            }

    @classmethod
    def log_full_changes(cls, project_id, project_data, new_project_data, user):
        # TODO: 'properties'
        diff_data = remove_empty_keys_from_dict({
            'details': cls._track_details(project_data, new_project_data),
            'organizations': get_flat_dict_diff(
                project_data['organizations'],
                new_project_data['organizations'],
                ['organization', 'organization_type'],
            ),
            'regions': get_list_diff(project_data['regions'], new_project_data['regions']),
            'memberships': {
                "users": get_list_diff(project_data['member_users'], new_project_data['member_users']),
                "user_groups": get_list_diff(project_data['member_user_groups'], new_project_data['member_user_groups'])
            },
            'framework': cls._track_framework(project_data, new_project_data)
        })

        if diff_data:
            action = ProjectChangeLog.Action.MULTIPLE
            changed_fields = list(diff_data.keys())
            if len(changed_fields) == 1:
                action = cls.ACTION_MAP[changed_fields[0]]
            return ProjectChangeLog.objects.create(
                project_id=project_id,
                user=user,
                action=action,
                diff=diff_data,
            )

    # Custom logger
    @classmethod
    def log_framework_update(cls, af_id, user):
        """
        Flag that an AF is updated to each project.
        """
        project_ids = Project.objects\
            .filter(analysis_framework=af_id)\
            .values_list('id', flat=True)
        change_logs = [
            ProjectChangeLog(
                user=user,
                project_id=project_id,
                action=ProjectChangeLog.Action.FRAMEWORK,
                diff={
                    'framework': {
                        'updated': True,
                    },
                },
            )
            for project_id in project_ids
        ]
        return ProjectChangeLog.objects.bulk_create(change_logs)

    @classmethod
    def log_project_created(cls, project, user):
        return ProjectChangeLog.objects.create(
            user=user,
            project=project,
            action=ProjectChangeLog.Action.PROJECT_CREATE,
        )
