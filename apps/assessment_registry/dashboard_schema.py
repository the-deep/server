import graphene
from dataclasses import dataclass
from collections import defaultdict


from django.db.models import Count, Sum
from django.db import models
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db.models.functions import TruncDay
from django.db import connection as django_db_connection

from deep.caches import CacheHelper
from geo.models import GeoArea
from utils.graphene.enums import EnumDescription
from .enums import (
    AssessmentRegistryAffectedGroupTypeEnum,
    AssessmentRegistryCoordinationTypeEnum,
    AssessmentRegistryDataCollectionTechniqueTypeEnum,
    AssessmentRegistryFocusTypeEnum,
    AssessmentRegistryProtectionInfoTypeEnum,
    AssessmentRegistrySectorTypeEnum,
    AssessmentRegistryUnitOfAnalysisTypeEnum,
    AssessmentRegistryUnitOfReportingTypeEnum,
    AssessmentRegistrySamplingApproachTypeEnum,
    AssessmentRegistryProximityTypeEnum,
)
from deep_explore.schema import count_by_date_queryset_generator
from .filter_set import (
    AssessmentDashboardFilterDataInputType,
    AssessmentDashboardFilterSet,
)
from .models import AssessmentRegistry, AssessmentRegistryOrganization, MethodologyAttribute


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
    coordinated_joint_display = EnumDescription(required=False, source="get_coordinated_joint_display")
    count = graphene.Int()


class StakeholderCountType(graphene.ObjectType):
    stakeholder = graphene.String()
    count = graphene.Int()


class CollectionTechniqueCountType(graphene.ObjectType):
    data_collection_technique = graphene.Field(AssessmentRegistryDataCollectionTechniqueTypeEnum, required=True)
    data_collection_technique_display = EnumDescription(source="get_data_collection_techniques_display", required=False)
    count = graphene.Int(required=True)


class AssessmentDashboardGeographicalAreaType(graphene.ObjectType):
    admin_level_id = graphene.ID(required=False)
    code = graphene.ID(required=False)
    count = graphene.ID(required=False)
    assessment_ids = graphene.List(graphene.NonNull(graphene.ID))


class AssessmentCountByDateType(graphene.ObjectType):
    date = graphene.Date(required=False)
    count = graphene.Int(required=False)


class AssessmentFocusCountByDateType(AssessmentCountByDateType):
    focus = graphene.Field(AssessmentRegistryFocusTypeEnum)


class AssessmentAffectedGroupCountByDateType(AssessmentCountByDateType):
    affected_group = graphene.Field(AssessmentRegistryAffectedGroupTypeEnum)


class AssessmentHumanitrainSectorCountByDateType(AssessmentCountByDateType):
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum)


class AssessmentProtectionInformationCountByDateType(AssessmentCountByDateType):
    protection_management = graphene.Field(AssessmentRegistryProtectionInfoTypeEnum)


class AssessmentPerAffectedGroupAndSectorCountByDateType(AssessmentCountByDateType):
    affected_group = graphene.Field(AssessmentRegistryAffectedGroupTypeEnum)
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum)


class AssessmentPerAffectedGroupAndGeoAreaCountByDateType(AssessmentCountByDateType):
    affected_group = graphene.Field(AssessmentRegistryAffectedGroupTypeEnum)
    locations = graphene.Int(required=False)


class AssessmentPerSectorAndGeoAreaCountByDateType(AssessmentCountByDateType):
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum)
    locations = graphene.Int(required=False)


class AssessmentByLeadOrganizationCountByDateType(AssessmentCountByDateType):
    organization = graphene.Int(required=False)


class AssessmentPerDataCollectionTechniqueCountByDateType(AssessmentCountByDateType):
    data_collection_technique = graphene.Field(AssessmentRegistryDataCollectionTechniqueTypeEnum)


class AssessmentPerUnitofAnalysisCountByDateType(AssessmentCountByDateType):
    unit_of_analysis = graphene.Field(AssessmentRegistryUnitOfAnalysisTypeEnum)


class AssessmentPerUnitofReportingCountByDateType(AssessmentCountByDateType):
    unit_of_reporting = graphene.Field(AssessmentRegistryUnitOfReportingTypeEnum)


class AssessmentPerSamplingApproachCountByDateType(AssessmentCountByDateType):
    sampling_approach = graphene.Field(AssessmentRegistrySamplingApproachTypeEnum)


class AssessmentPerProximityCountByDateType(AssessmentCountByDateType):
    proximity = graphene.Field(AssessmentRegistryProximityTypeEnum)


class SamplingSizeAssessmentPerDataCollectionTechniqueCountByDateType(graphene.ObjectType):
    date = graphene.Date(required=False)
    sampling_size = graphene.Int(required=False)
    data_collection_technique = graphene.Field(AssessmentRegistryDataCollectionTechniqueTypeEnum)


class AssessmentDashboardStatisticsType(graphene.ObjectType):
    total_assessment = graphene.Int(required=True)
    total_stakeholder = graphene.Int(required=True)
    total_collection_technique = graphene.Int(required=True)
    assessment_count = graphene.List(AssessmentCountType)
    stakeholder_count = graphene.List(StakeholderCountType)
    collection_technique_count = graphene.List(CollectionTechniqueCountType)
    total_multisector_assessment = graphene.Int(required=True)
    total_singlesector_assessment = graphene.Int(required=True)
    assessment_geographic_areas = graphene.List(AssessmentDashboardGeographicalAreaType)
    assessment_by_over_time = graphene.List(AssessmentCountByDateType)
    assessment_per_framework_piller = graphene.List(AssessmentFocusCountByDateType)
    assessment_per_affected_group = graphene.List(AssessmentAffectedGroupCountByDateType)
    assessment_per_humanitarian_sector = graphene.List(AssessmentHumanitrainSectorCountByDateType)
    assessment_per_protection_management = graphene.List(AssessmentProtectionInformationCountByDateType)
    assessment_per_affected_group_and_sector = graphene.List(AssessmentPerAffectedGroupAndSectorCountByDateType)
    assessment_per_affected_group_and_geoarea = graphene.List(AssessmentPerAffectedGroupAndGeoAreaCountByDateType)
    assessment_per_sector_and_geoarea = graphene.List(AssessmentPerSectorAndGeoAreaCountByDateType)
    assessment_by_lead_organization = graphene.List(AssessmentByLeadOrganizationCountByDateType)
    assessment_per_datatechnique = graphene.List(AssessmentPerDataCollectionTechniqueCountByDateType)
    assessment_per_unit_of_analysis = graphene.List(AssessmentPerUnitofAnalysisCountByDateType)
    assessment_per_unit_of_reporting = graphene.List(AssessmentPerUnitofReportingCountByDateType)
    assessment_per_sampling_approach = graphene.List(AssessmentPerSamplingApproachCountByDateType)
    assessment_per_proximity = graphene.List(AssessmentPerProximityCountByDateType)
    sample_size_per_data_collection_technique = graphene.List(
        SamplingSizeAssessmentPerDataCollectionTechniqueCountByDateType
    )

    @staticmethod
    def custom_resolver(root, info, _filter):
        assessment_qs = AssessmentRegistry.objects.filter(
            project=info.context.active_project,
            **get_global_filters(_filter),
        )
        assessment_qs_filter = AssessmentDashboardFilterSet(queryset=assessment_qs, data=_filter.get("assessment")).qs
        methodology_attribute_qs = MethodologyAttribute.objects.filter(assessment_registry__in=assessment_qs_filter)
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
        qs = root.assessment_registry_qs.values("stakeholders").distinct()
        return qs.count()

    @staticmethod
    def resolve_total_collection_technique(root: AssessmentDashboardStat, info) -> int:
        return root.methodology_attribute_qs.values("data_collection_technique").distinct().count()

    @staticmethod
    def resolve_assessment_count(root: AssessmentDashboardStat, info):
        assessment = (
            root.assessment_registry_qs.values("coordinated_joint")
            .annotate(count=Count("coordinated_joint"))
            .order_by("coordinated_joint")
        )
        return assessment

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
        return (
            root.methodology_attribute_qs.values("data_collection_technique")
            .annotate(count=Count("data_collection_technique"))
            .order_by("data_collection_technique")
        )

    @staticmethod
    def resolve_total_multisector_assessment(root: AssessmentDashboardStat, info) -> int:
        return root.assessment_registry_qs.filter(sectors__len__gte=2).count()

    @staticmethod
    def resolve_total_singlesector_assessment(root: AssessmentDashboardStat, info) -> int:
        return root.assessment_registry_qs.filter(sectors__len=1).count()

    @staticmethod
    def resolve_assessment_geographic_areas(root: AssessmentDashboardStat, info):
        return (
            GeoArea.objects.annotate(
                assessment_ids=ArrayAgg(
                    "focus_location_assessment_reg",
                    ordering="focus_location_assessment_reg",
                    distinct=True,
                    filter=models.Q(focus_location_assessment_reg__in=root.assessment_registry_qs),
                ),
                count=Count("focus_location_assessment_reg", distinct=True),
            )
            .filter(focus_location_assessment_reg__isnull=False)
            .values("admin_level_id", "code", "count", "assessment_ids")
        )

    @staticmethod
    def resolve_assessment_by_over_time(root: AssessmentDashboardStat, info):
        return count_by_date_queryset_generator(root.assessment_registry_qs, TruncDay)

    @staticmethod
    def resolve_assessment_per_framework_piller(root: AssessmentDashboardStat, info):
        return root.assessment_registry_qs.values(date=TruncDay("created_at")).annotate(
            count=Count("id"),
            focus=models.Func(models.F("focuses"), function="unnest"),
        )

    @staticmethod
    def resolve_assessment_per_affected_group(root: AssessmentDashboardStat, info):
        return root.assessment_registry_qs.values(date=TruncDay("created_at")).annotate(
            count=Count("id"),
            affected_group=models.Func(models.F("affected_groups"), function="unnest"),
        )

    @staticmethod
    def resolve_assessment_per_humanitarian_sector(root: AssessmentDashboardStat, info):
        return root.assessment_registry_qs.values(date=TruncDay("created_at")).annotate(
            count=Count("id"),
            sector=models.Func(models.F("sectors"), function="unnest"),
        )

    @staticmethod
    def resolve_assessment_per_protection_management(root: AssessmentDashboardStat, info):
        return root.assessment_registry_qs.values(date=TruncDay("created_at")).annotate(
            count=Count("id"),
            protection_management=models.Func(models.F("protection_info_mgmts"), function="unnest"),
        )

    @staticmethod
    def resolve_assessment_per_affected_group_and_sector(root: AssessmentDashboardStat, info):
        # TODO : Global filter and assessment filter need to implement
        with django_db_connection.cursor() as cursor:
            query = """
                SELECT
                    sector,
                    affected_group,
                    Count(*) as count
                FROM (
                    select
                        -- Only select required fields
                        id,
                        sectors,
                        affected_groups
                 FROM assessment_registry_assessmentregistry
                    -- Only process required rows
                ) as t
                CROSS JOIN unnest(t.sectors) AS sector
                CROSS JOIN unnest(t.affected_groups) AS affected_group
                GROUP BY sector, affected_group
                ORDER BY sector, affected_group DESC;
                """
            cursor.execute(query, {})
            return [
                AssessmentPerAffectedGroupAndSectorCountByDateType(sector=data[0], affected_group=data[1], count=data[2])
                for data in cursor.fetchall()
            ]

    @staticmethod
    def resolve_assessment_per_affected_group_and_geoarea(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.values("locations", date=TruncDay("created_at"))
            .annotate(
                count=Count("id"),
                affected_group=models.Func(models.F("affected_groups"), function="unnest"),
            )
            .filter(locations__admin_level__level=1)
            .values("locations", "affected_group", "count", "date")
            .order_by("count")[:10]
        )

    @staticmethod
    def resolve_assessment_per_sector_and_geoarea(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.values("locations")
            .annotate(
                count=Count("id"),
                sector=models.Func(models.F("sectors"), function="unnest"),
            )
            .filter(locations__admin_level__level=1)
            .values("locations", "sector", "count")
            .order_by("count")[:10]
        )

    @staticmethod
    def resolve_assessment_by_lead_organization(root: AssessmentDashboardStat, info):
        return (
            AssessmentRegistryOrganization.objects.filter(
                organization_type=AssessmentRegistryOrganization.Type.LEAD_ORGANIZATION
            )
            .filter(assessment_registry__in=root.assessment_registry_qs)
            .annotate(count=Count("organization"))
            .values("organization", "count", date=TruncDay("assessment_registry__created_at"))
        )

    @staticmethod
    def resolve_assessment_per_datatechnique(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(count=Count("data_collection_technique"))
            .values("data_collection_technique", "count", "date")
            .order_by("data_collection_technique")
        )

    @staticmethod
    def resolve_assessment_per_unit_of_analysis(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(count=Count("unit_of_analysis"))
            .values("unit_of_analysis", "count", "date")
            .order_by("unit_of_analysis")
        )

    @staticmethod
    def resolve_assessment_per_unit_of_reporting(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(count=Count("unit_of_reporting"))
            .values("unit_of_reporting", "count", "date")
            .order_by("unit_of_reporting")
        )

    @staticmethod
    def resolve_assessment_per_sampling_approach(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(count=Count("sampling_approach"))
            .values("sampling_approach", "count", "date")
            .order_by("sampling_approach")
        )

    @staticmethod
    def resolve_assessment_per_proximity(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(count=Count("proximity"))
            .values("proximity", "count", "date")
            .order_by("proximity")
        )

    @staticmethod
    def resolve_sample_size_per_data_collection_technique(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(sampling_size=Sum("sampling_size"))
            .values("sampling_size", "data_collection_technique", "date")
            .order_by("data_collection_technique")
        )


class Query:
    assessment_dashboard_statistics = graphene.Field(
        AssessmentDashboardStatisticsType,
        filter=AssessmentDashboardFilterInputType(required=True),
    )

    @staticmethod
    def resolve_assessment_dashboard_statistics(root, info, filter):
        return AssessmentDashboardStatisticsType.custom_resolver(root, info, filter)
