import graphene
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db import models
from django.db.models.functions import Cast, Coalesce
from graphene_django import DjangoObjectType

from deep.serializers import URLCachedFileField
from utils.graphene.types import CustomDjangoListObjectType

from .filter_set import PublicProjectGqlFilterSet
from .models import Project


class PublicProjectType(DjangoObjectType):
    class Meta:
        model = Project
        skip_registry = True
        fields = (
            "id",
            "title",
            "description",
            "created_at",
        )

    analysis_framework = graphene.ID(source="analysis_framework_id")
    analysis_framework_title = graphene.String()
    regions_title = graphene.String()
    organizations_title = graphene.String()
    number_of_users = graphene.Int(required=True)
    number_of_leads = graphene.Int(required=True)
    number_of_entries = graphene.Int(required=True)
    analysis_framework_preview_image = graphene.String()

    @staticmethod
    def resolve_analysis_framework_preview_image(root, info, **kwargs):
        if root.preview_image:
            return info.context.request.build_absolute_uri(URLCachedFileField.name_to_representation(root.preview_image))
        return None


class PublicProjectListType(CustomDjangoListObjectType):
    class Meta:
        model = Project
        base_type = PublicProjectType
        filterset_class = PublicProjectGqlFilterSet

    @classmethod
    def queryset(cls):
        return (
            Project.objects.filter(
                is_deleted=False,
                is_private=False,
                is_test=False,
            )
            .annotate(
                analysis_framework_title=models.Case(
                    models.When(analysis_framework__is_private=False, then=models.F("analysis_framework__title")),
                    default=None,
                ),
                preview_image=models.Case(
                    models.When(analysis_framework__is_private=False, then=models.F("analysis_framework__preview_image")),
                    default=None,
                ),
                regions_title=StringAgg(
                    "regions__title",
                    ", ",
                    filter=models.Q(
                        ~models.Q(regions__title=""),
                        regions__public=True,
                        regions__title__isnull=False,
                    ),
                    distinct=True,
                ),
                organizations_title=StringAgg(
                    models.Case(
                        models.When(
                            projectorganization__organization__parent__isnull=False,
                            then="projectorganization__organization__parent__title",
                        ),
                        default="projectorganization__organization__title",
                    ),
                    ", ",
                    distinct=True,
                ),
                **{
                    key: Coalesce(
                        Cast(KeyTextTransform(key, "stats_cache"), models.IntegerField()),
                        0,
                    )
                    for key in ["number_of_leads", "number_of_users", "number_of_entries"]
                },
            )
            .only(
                "id",
                "title",
                "description",
                "analysis_framework_id",
                "created_at",
            )
            .distinct()
        )


class PublicProjectWithMembershipData(graphene.ObjectType):
    id = graphene.ID(required=True)
    title = graphene.ID(required=True)
    membership_pending = graphene.Boolean(required=True)
    is_rejected = graphene.Boolean(required=True)

    @staticmethod
    def resolve_membership_pending(root, info):
        return info.context.dl.project.join_status.load(root.pk)

    @staticmethod
    def resolve_is_rejected(root, info):
        return info.context.dl.project.project_rejected_status.load(root.pk)
