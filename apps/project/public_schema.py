import graphene

from graphene_django import DjangoObjectType
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models.functions import Cast, Coalesce
from django.db import models

from utils.graphene.types import CustomDjangoListObjectType

from .models import Project
from .filter_set import ProjectGqlFilterSet


class PublicProjectType(DjangoObjectType):
    class Meta:
        model = Project
        skip_registry = True
        fields = (
            'id',
            'title',
            'description',
            'analysis_framework_id',
            'created_at',
        )

    analysis_framework_title = graphene.String()
    regions_title = graphene.String()
    organizations_title = graphene.String()
    number_of_users = graphene.Int(required=True)
    number_of_leads = graphene.Int(required=True)
    number_of_entries = graphene.Int(required=True)


class PublicProjectListType(CustomDjangoListObjectType):
    class Meta:
        model = Project
        base_type = PublicProjectType
        filterset_class = ProjectGqlFilterSet

    @classmethod
    def queryset(cls):
        return Project.objects.filter(is_private=False).annotate(
            analysis_framework_title=models.F('analysis_framework__title'),
            regions_title=StringAgg('regions__title', ', ', distinct=True),
            organizations_title=StringAgg(
                models.Case(
                    models.When(
                        projectorganization__organization__parent__isnull=False,
                        then='projectorganization__organization__parent__title'
                    ),
                    default='projectorganization__organization__title',
                ),
                ', ',
                distinct=True,
            ),
            **{
                key: Coalesce(
                    Cast(KeyTextTransform(key, 'stats_cache'), models.IntegerField()),
                    0,
                )
                for key in ['number_of_leads', 'number_of_users', 'number_of_entries']
            },
        ).only(
            'id',
            'title',
            'description',
            'analysis_framework_id',
            'created_at',
        )
