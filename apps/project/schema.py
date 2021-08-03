from typing import List

import graphene
from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.permissions import ProjectPermissions as PP
from lead.schema import Query as LeadQuery
from export.schema import Query as ExportQuery

from .models import Project
from .filter_set import ProjectFilterSet


class ProjectType(DjangoObjectType):
    class Meta:
        model = Project
        fields = (
            'id', 'title', 'description', 'start_date', 'end_date',
            'regions', 'analysis_framework', 'assessment_template',
            'is_default', 'is_private', 'is_visualization_enabled', 'status',
            'organizations', 'stats_cache',
        )

    current_user_role = graphene.String()

    # NOTE: This is a custom feature
    # see: https://github.com/eamigo86/graphene-django-extras/compare/graphene-v2...the-deep:graphene-v2
    @staticmethod
    def get_custom_node(_, info, id):
        try:
            project = Project.get_for_gq(info.context.user).get(pk=id)
            info.context.set_active_project(project)
            return project
        except Project.DoesNotExist:
            return None


class ProjectDetailType(
    # -- Start --Project scopped entities
    LeadQuery,
    ExportQuery,
    # --  End  --Project scopped entities
    ProjectType,
):
    allowed_permissions = graphene.List(
        graphene.NonNull(
            graphene.Enum.from_enum(PP.Permission),
        ), required=True
    )

    class Meta:
        model = Project
        skip_registry = True
        fields = (
            'id', 'title', 'description', 'start_date', 'end_date',
            'members', 'regions', 'user_groups', 'analysis_framework',
            'category_editor', 'assessment_template', 'data',
            'is_default', 'is_private', 'is_visualization_enabled', 'status',
            'organizations', 'stats_cache',
            'allowed_permissions',
        )

    @staticmethod
    def resolve_allowed_permissions(root, info) -> List[str]:
        return info.context.project_permissions


class ProjectListType(CustomDjangoListObjectType):
    class Meta:
        model = Project
        filterset_class = ProjectFilterSet


class Query:
    project = DjangoObjectField(ProjectDetailType)
    projects = DjangoPaginatedListObjectField(
        ProjectListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    # NOTE: This is a custom feature, see https://github.com/the-deep/graphene-django-extras
    # see: https://github.com/eamigo86/graphene-django-extras/compare/graphene-v2...the-deep:graphene-v2
    @staticmethod
    def resolve_projects(root, info, **kwargs) -> QuerySet:
        return Project.get_for_gq(info.context.user).distinct()
