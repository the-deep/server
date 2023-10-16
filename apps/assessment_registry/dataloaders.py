from django.db.models import Count
from collections import defaultdict
from promise import Promise

from django.utils.functional import cached_property
from django.db import connection as django_db_connection
from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    AssessmentRegistryOrganization,
    SummaryIssue,
)


class AssessmentRegistryOrganizationsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AssessmentRegistryOrganization.objects.filter(assessment_registry__in=keys)
        _map = defaultdict(list)
        for org in qs.all():
            _map[org.assessment_registry_id].append(org)
        return Promise.resolve([_map.get(key) for key in keys])


class AssessmentRegistryIssueLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = SummaryIssue.objects.filter(id__in=keys)
        _map = {
            issue.pk: issue
            for issue in qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class AssessmentRegistryIssueChildLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = SummaryIssue.objects.filter(
            parent__in=keys
        ).values(
            'parent'
        ).annotate(
            child_count=Count(
                'parent'
            )
        ).values(
            'parent',
            'child_count'
        )

        counts_map = {
            obj['parent']: obj['child_count']
            for obj in qs
        }

        return Promise.resolve([counts_map.get(key, 0) for key in keys])


class SummaryIssueLevelLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        with django_db_connection.cursor() as cursor:
            select_sql = f'''
                WITH RECURSIVE parents AS (
                    SELECT
                        sub_g.id,
                        sub_g.id as main_entity_id,
                        sub_g.parent_id
                    FROM {SummaryIssue._meta.db_table} AS sub_g
                    WHERE
                        sub_g.id IN %s
                    UNION
                    SELECT
                        sub_parent_g.id,
                        parents.main_entity_id,
                        sub_parent_g.parent_id
                    FROM {SummaryIssue._meta.db_table} AS sub_parent_g
                        INNER JOIN parents ON sub_parent_g.id = parents.parent_id
                )
                SELECT
                    main_entity_id,
                    count(*)
                FROM parents
                GROUP BY main_entity_id
                '''
            cursor.execute(select_sql, (tuple(keys),))
            _map = {
                _id: level
                for _id, level in cursor.fetchall()
            }
        return Promise.resolve([_map.get(key, 0) for key in keys])


class DataLoaders(WithContextMixin):

    @cached_property
    def stakeholders(self):
        return AssessmentRegistryOrganizationsLoader(context=self.context)

    @cached_property
    def issues(self):
        return AssessmentRegistryIssueLoader(context=self.context)

    @cached_property
    def child_issues(self):
        return AssessmentRegistryIssueChildLoader(context=self.context)

    @cached_property
    def summary_issue_level(self):
        return SummaryIssueLevelLoader(context=self.context)
