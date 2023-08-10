import itertools
import graphene
from dataclasses import dataclass
from collections import defaultdict

from django.db.models import Count
from django.db import models
from django.contrib.postgres.aggregates.general import ArrayAgg

from deep.caches import CacheHelper
from geo.models import Region, GeoArea
from utils.graphene.filters import IDListFilter
from utils.graphene.enums import EnumDescription
from utils.graphene.geo_scalars import PointScalar
from .enums import (
    AssessmentRegistryCoordinationTypeEnum,
    AssessmentRegistryDataCollectionTechniqueTypeEnum,
)
from .filter_set import (
    AssessmentDashboardFilterDataInputType,
    AssessmentDashboardFilterSet,
)
from .models import AssessmentRegistry, MethodologyAttribute


def get_global_filters(_filter: dict, date_field="created_at"):
    return {
        f"{date_field}__gte": _filter["date_from"],
        f"{date_field}__lte": _filter["date_to"],
    }


@dataclass
class AssessmentDashboardStat:
    cache_key: str
    assessment_registry_qs: models.QuerySet
    methodology_attribute_qs: models.QuerySet


class AssessmentDashboardFilterInputType(graphene.InputObjectType):
    date_from = graphene.Date(required=True)
    date_to = graphene.Date(required=True)
    assessment = AssessmentDashboardFilterDataInputType()


class AssessmentCountType(graphene.ObjectType):
    coordinated_joint = graphene.Field(AssessmentRegistryCoordinationTypeEnum)
    coordinated_joint_display = EnumDescription(required=False)
    count = graphene.Int()

    def resolve_coordinated_joint_display(self, info):
        return AssessmentRegistry.CoordinationType(self.coordinated_joint).label


class StakeholderCountType(graphene.ObjectType):
    stakeholder = graphene.String()
    count = graphene.Int()


class CollectionTechniqueCountType(graphene.ObjectType):
    data_collection_technique = graphene.Field(
        AssessmentRegistryDataCollectionTechniqueTypeEnum, required=True
    )
    data_collection_technique_display = EnumDescription(required=False)
    count = graphene.Int(required=True)

    def resolve_data_collection_technique_display(self, info):
        return MethodologyAttribute.CollectionTechniqueType(
            self.data_collection_technique
        ).label


class AssessmentDashboardGeographicalArea(graphene.ObjectType):
    admin_level_id = graphene.ID(required=False)
    code=graphene.ID(required=False)
    count=graphene.ID(required=False)
    assessment_ids = graphene.List(graphene.NonNull(graphene.ID))


class AssessmentDashboardStatisticsType(graphene.ObjectType):
    total_assessment = graphene.Int(required=True)
    total_stakeholder = graphene.Int(required=True)
    total_collection_technique = graphene.Int(required=True)
    assessment_count = graphene.List(AssessmentCountType)
    stakeholder_count = graphene.List(StakeholderCountType)
    collection_technique_count = graphene.List(CollectionTechniqueCountType)
    total_multisector_assessment = graphene.Int(required=True)
    total_singlesector_assessment = graphene.Int(required=True)
    assessment_geographic_areas = graphene.List(AssessmentDashboardGeographicalArea)

    @staticmethod
    def custom_resolver(root, info, _filter):
        assessment_qs = AssessmentRegistry.objects.filter(
            project=info.context.active_project,
            **get_global_filters(_filter),
        )
        assessment_qs_filter = AssessmentDashboardFilterSet(
            queryset=assessment_qs, data=_filter.get("assessment")
        ).qs
        methodology_attribute_qs = MethodologyAttribute.objects.filter(
            assessment_registry__in=assessment_qs_filter
        )
        cache_key = CacheHelper.generate_hash(_filter.__dict__)
        return AssessmentDashboardStat(
            cache_key=cache_key,
            assessment_registry_qs=assessment_qs_filter,
            methodology_attribute_qs=methodology_attribute_qs,
        )

    @staticmethod
    def resolve_total_assessment(root: AssessmentDashboardStat, info) -> int:
        return root.assessment_registry_qs.count()

    @staticmethod
    def resolve_total_stakeholder(root: AssessmentDashboardStat, info) -> int:
        qs = root.assessment_registry_qs.values("stakeholders")
        return qs.count()

    @staticmethod
    def resolve_total_collection_technique(root: AssessmentDashboardStat, info) -> int:
        return (
            root.methodology_attribute_qs.values("data_collection_technique")
            .distinct()
            .count()
        )

    @staticmethod
    def resolve_assessment_count(root: AssessmentDashboardStat, info):
        assessment = (
            root.assessment_registry_qs.values("coordinated_joint")
            .annotate(count=Count("coordinated_joint"))
            .order_by("coordinated_joint")
        )

        return [
            AssessmentCountType(
                coordinated_joint=assessment["coordinated_joint"],
                count=assessment["count"],
            )
            for assessment in assessment
        ]

    @staticmethod
    def resolve_stakeholder_count(root: AssessmentDashboardStat, info):
        stakeholder_counts = defaultdict(int)
        organization_type_fields = ["stakeholders__organization_type__title"]

        for field in organization_type_fields:
            stakeholders = root.assessment_registry_qs.values(field)
            for stakeholder in stakeholders:
                if organization_type_title := stakeholder.get(field):
                    stakeholder_counts[organization_type_title] += 1
        return [
            StakeholderCountType(
                stakeholder=org_type_title,
                count=count,
            )
            for org_type_title, count in stakeholder_counts.items()
        ]

    @staticmethod
    def resolve_collection_technique_count(root: AssessmentDashboardStat, info):
        data_collection_technique = (
            root.methodology_attribute_qs.values("data_collection_technique")
            .annotate(count=Count("data_collection_technique"))
            .order_by("data_collection_technique")
        )
        return [
            CollectionTechniqueCountType(
                data_collection_technique=technique["data_collection_technique"],
                count=technique["count"],
            )
            for technique in data_collection_technique
        ]

    @staticmethod
    def resolve_total_multisector_assessment(root: AssessmentDashboardStat, info) -> int:
        return root.assessment_registry_qs.filter(sectors__len__gte=2).count()

    @staticmethod
    def resolve_total_singlesector_assessment(root: AssessmentDashboardStat, info) -> int:
        return root.assessment_registry_qs.filter(sectors__len=1).count()
    
    @staticmethod
    def resolve_assessment_geographic_areas(root: AssessmentDashboardStat, info):
        return GeoArea.objects.annotate(
            assessment_ids=ArrayAgg(
                'focus_location_assessment_reg',
                ordering='focus_location_assessment_reg',
                distinct=True,
                filter=models.Q(focus_location_assessment_reg__in=root.assessment_registry_qs),
            ),
            count=Count('focus_location_assessment_reg',distinct=True)
        ).filter(focus_location_assessment_reg__isnull=False).values(
            'admin_level_id',
            'code',
            'count',
            'assessment_ids'
        )

class Query:
    assessment_dashboard_statistics = graphene.Field(
        AssessmentDashboardStatisticsType,
        filter=AssessmentDashboardFilterInputType(),
    )

    @staticmethod
    def resolve_assessment_dashboard_statistics(root, info, filter):
        return AssessmentDashboardStatisticsType.custom_resolver(root, info, filter)
