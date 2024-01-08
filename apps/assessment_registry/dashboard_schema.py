import graphene
from dataclasses import dataclass

from django.db.models import Count, Sum, Avg, Case, Value, When
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db import models
from django.db.models.functions import TruncDay, TruncMonth
from django.db import connection as django_db_connection
from geo.schema import ProjectGeoAreaType


from deep.caches import CacheHelper, CacheKey
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
    AssessmentRegistryScoreCriteriaTypeEnum,
)
from deep_explore.schema import count_by_date_queryset_generator
from .filter_set import (
    AssessmentDashboardFilterDataInputType,
    AssessmentDashboardFilterSet,
)
from .models import (
    AssessmentRegistry,
    AssessmentRegistryOrganization,
    MethodologyAttribute,
)
from organization.schema import OrganizationType as OrganizationObjectType

# TODO?
NODE_CACHE_TIMEOUT = 60 * 60 * 1


def node_cache(cache_key):
    def cache_key_gen(root: AssessmentDashboardStat, *_):
        return root.cache_key
    return CacheHelper.gql_cache(
        cache_key,
        timeout=NODE_CACHE_TIMEOUT,
        cache_key_gen=cache_key_gen,
    )


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
    coordinated_joint = graphene.Field(AssessmentRegistryCoordinationTypeEnum, required=True)
    coordinated_joint_display = EnumDescription(required=True)
    count = graphene.Int()

    def resolve_coordinated_joint_display(root, info):
        return AssessmentRegistry.CoordinationType(root["coordinated_joint"]).label


class StakeholderCountType(graphene.ObjectType):
    stakeholder = graphene.String(required=True)
    count = graphene.Int()


class CollectionTechniqueCountType(graphene.ObjectType):
    data_collection_technique = graphene.Field(AssessmentRegistryDataCollectionTechniqueTypeEnum, required=True)
    data_collection_technique_display = EnumDescription(required=True)  # Note resolver is used to get the enum values
    count = graphene.Int(required=True)

    def resolve_data_collection_technique_display(root, info):
        return MethodologyAttribute.CollectionTechniqueType(root["data_collection_technique"]).label


class AssessmentDashboardGeographicalAreaType(graphene.ObjectType):
    region = graphene.ID(required=True)
    geo_area = graphene.ID(required=True)
    admin_level_id = graphene.ID(required=True)
    code = graphene.ID(required=True)
    count = graphene.Int(required=True)
    assessment_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)


class AssessmentCountByDateType(graphene.ObjectType):
    date = graphene.Date(required=True)
    count = graphene.Int(required=True)


class AssessmentFocusCountByDateType(AssessmentCountByDateType):
    focus = graphene.Field(AssessmentRegistryFocusTypeEnum, required=True)
    focus_display = EnumDescription(required=True)

    def resolve_focus_display(root, info):
        return AssessmentRegistry.FocusType(root["focus"]).label


class AssessmentAffectedGroupCountByDateType(AssessmentCountByDateType):
    affected_group = graphene.Field(AssessmentRegistryAffectedGroupTypeEnum, required=True)
    affected_group_display = EnumDescription(required=True)

    def resolve_affected_group_display(root, info):
        return AssessmentRegistry.AffectedGroupType(root["affected_group"]).label


class AssessmentHumanitrainSectorCountByDateType(AssessmentCountByDateType):
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum, required=True)
    sector_display = EnumDescription(required=True)

    def resolve_sector_display(root, info):
        return AssessmentRegistry.SectorType(root["sector"]).label


class AssessmentProtectionInformationCountByDateType(AssessmentCountByDateType):
    protection_management = graphene.Field(AssessmentRegistryProtectionInfoTypeEnum, required=True)
    protection_management_display = graphene.String(required=True)

    def resolve_protection_management_display(root, info):
        return AssessmentRegistry.ProtectionInfoType(root["protection_management"]).label


class AssessmentPerAffectedGroupAndSectorCountByDateType(graphene.ObjectType):
    affected_group = graphene.Field(AssessmentRegistryAffectedGroupTypeEnum, required=True)
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum, required=True)
    count = graphene.Int(required=True)


class AssessmentPerAffectedGroupAndGeoAreaCountByDateType(AssessmentCountByDateType):
    affected_group = graphene.Field(AssessmentRegistryAffectedGroupTypeEnum, required=True)
    geo_area = graphene.Field(ProjectGeoAreaType, required=True)
    affected_group_display = EnumDescription(required=True)

    def resolve_geo_area(root, info):
        return info.context.dl.assessment_registry.geo_area.load(root["geo_area"])

    def resolve_affected_group_display(root, info):
        return AssessmentRegistry.AffectedGroupType(root["affected_group"]).label


class AssessmentPerSectorAndGeoAreaCountByDateType(graphene.ObjectType):
    count = graphene.Int(required=True)
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum, required=True)
    geo_area = graphene.Field(ProjectGeoAreaType, required=True)
    sector_display = EnumDescription(required=True)

    def resolve_geo_area(root, info):
        return info.context.dl.assessment_registry.geo_area.load(root["geo_area"])

    def resolve_sector_display(root, info):
        return AssessmentRegistry.SectorType(root["sector"]).label


class AssessmentByLeadOrganizationCountByDateType(AssessmentCountByDateType):
    organization = graphene.Field(OrganizationObjectType, required=True)

    def resolve_organization(root, info):
        return info.context.dl.organization.organization.load(root["organization"])


class AssessmentPerDataCollectionTechniqueCountByDateType(AssessmentCountByDateType):
    data_collection_technique = graphene.Field(AssessmentRegistryDataCollectionTechniqueTypeEnum, required=True)
    data_collection_technique_display = EnumDescription(required=True)

    def resolve_data_collection_technique_display(root, info):
        return MethodologyAttribute.CollectionTechniqueType(root["data_collection_technique"]).label


class AssessmentPerUnitofAnalysisCountByDateType(AssessmentCountByDateType):
    unit_of_analysis = graphene.Field(AssessmentRegistryUnitOfAnalysisTypeEnum, required=True)
    unit_of_analysis_display = EnumDescription(required=True)

    def resolve_unit_of_analysis_display(root, info):
        return MethodologyAttribute.UnitOfAnalysisType(root["unit_of_analysis"]).label


class AssessmentPerUnitofReportingCountByDateType(AssessmentCountByDateType):
    unit_of_reporting = graphene.Field(AssessmentRegistryUnitOfReportingTypeEnum, required=True)
    unit_of_reporting_display = EnumDescription(required=True)

    def resolve_unit_of_reporting_display(root, info):
        return MethodologyAttribute.UnitOfReportingType(root["unit_of_reporting"]).label


class AssessmentPerSamplingApproachCountByDateType(AssessmentCountByDateType):
    sampling_approach = graphene.Field(AssessmentRegistrySamplingApproachTypeEnum, required=True)
    sampling_approach_display = EnumDescription(required=True)

    def resolve_sampling_approach_display(root, info):
        return MethodologyAttribute.SamplingApproachType(root["sampling_approach"]).label


class AssessmentPerProximityCountByDateType(AssessmentCountByDateType):
    proximity = graphene.Field(AssessmentRegistryProximityTypeEnum, required=True)
    proximity_display = EnumDescription(required=True)

    def resolve_proximity_display(root, info):
        return MethodologyAttribute.ProximityType(root["proximity"]).label


class SamplingSizeAssessmentPerDataCollectionTechniqueCountByDateType(graphene.ObjectType):
    date = graphene.Date(required=True)
    sampling_size = graphene.Int(required=True)
    data_collection_technique = graphene.Field(AssessmentRegistryDataCollectionTechniqueTypeEnum, required=True)
    data_collection_technique_display = EnumDescription(required=True)

    def resolve_data_collection_technique_display(root, info):
        return MethodologyAttribute.CollectionTechniqueType(root["data_collection_technique"]).label


class AssessmentByGeographicalAndDataCollectionTechniqueCountByDateType(graphene.ObjectType):
    admin_level_id = graphene.ID(required=True)
    region = graphene.ID(required=True)
    geo_area = graphene.ID(required=True)
    data_collection_technique = graphene.Field(AssessmentRegistryDataCollectionTechniqueTypeEnum, required=True)
    count = graphene.Int(required=True)
    data_collection_technique_display = EnumDescription(required=True)

    def resolve_data_collection_technique_display(root, info):
        return MethodologyAttribute.CollectionTechniqueType(root["data_collection_technique"]).label


class AssessmentByGeographicalAndSamplingApproachCountByDateType(graphene.ObjectType):
    admin_level_id = graphene.ID(required=True)
    region = graphene.ID(required=True)
    geo_area = graphene.ID(required=True)
    sampling_approach = graphene.Field(AssessmentRegistrySamplingApproachTypeEnum, required=True)
    count = graphene.Int(required=True)
    sampling_approach_display = EnumDescription(required=True)

    def resolve_sampling_approach_display(root, info):
        return MethodologyAttribute.SamplingApproachType(root["sampling_approach"]).label


class AssessmentByGeographicalAndProximityCountByDateType(graphene.ObjectType):
    admin_level_id = graphene.ID(required=True)
    region = graphene.ID(required=True)
    geo_area = graphene.ID(required=True)
    proximity = graphene.Field(AssessmentRegistryProximityTypeEnum, required=True)
    count = graphene.Int(required=True)
    proximity_display = EnumDescription(required=True)

    def resolve_proximity_display(root, info):
        return MethodologyAttribute.ProximityType(root["proximity"]).label


class AssessmentByGeographicalAndUnit_Of_AnalysisCountByDateType(graphene.ObjectType):
    admin_level_id = graphene.ID(required=True)
    region = graphene.ID(required=True)
    geo_area = graphene.ID(required=True)
    unit_of_analysis = graphene.Field(AssessmentRegistryUnitOfAnalysisTypeEnum, required=True)
    count = graphene.Int(required=True)
    unit_of_analysis_display = EnumDescription(required=True)

    def resolve_unit_of_analysis_display(root, info):
        return MethodologyAttribute.UnitOfAnalysisType(root["unit_of_analysis"]).label


class AssessmentByGeographicalAndUnit_Of_ReportingCountByDateType(graphene.ObjectType):
    admin_level_id = graphene.ID(required=True)
    region = graphene.ID(required=True)
    geo_area = graphene.ID(required=True)
    unit_of_reporting = graphene.Field(AssessmentRegistryUnitOfReportingTypeEnum, required=True)
    count = graphene.Int(required=True)
    unit_of_reporting_display = EnumDescription(required=True)

    def resolve_unit_of_reporting_display(root, info):
        return MethodologyAttribute.UnitOfReportingType(root["unit_of_reporting"]).label


class MedianQualityScoreByGeographicalAreaDateType(graphene.ObjectType):
    admin_level_id = graphene.ID(required=True)
    region = graphene.ID(required=True)
    geo_area = graphene.ID(required=True)
    final_score = graphene.Float(required=True)


class MedianQualityScoreOverTimeDateType(graphene.ObjectType):
    date = graphene.Date(required=True)
    final_score = graphene.Float(required=True)


class MedianScoreOfEachDimensionType(graphene.ObjectType):
    final_score = graphene.Float(required=True)
    score_type = graphene.Field(AssessmentRegistryScoreCriteriaTypeEnum, required=True)


class MedianScoreOfEachDimensionDateType(MedianScoreOfEachDimensionType):
    date = graphene.Date(required=True)


class MedianScoreOfAnalyticalDensityType(graphene.ObjectType):
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum, required=True)
    final_score = graphene.Float(required=True)
    sector_display = EnumDescription(required=True)

    def resolve_sector_display(root, info):
        return AssessmentRegistry.SectorType(root["sector"]).label


class MedianScoreOfAnalyticalDensityDateType(MedianScoreOfAnalyticalDensityType):
    date = graphene.Date(required=True)


class MedianScoreOfGeographicalAndSectorDateType(graphene.ObjectType):
    date = graphene.Date(required=True)
    final_score = graphene.Float(required=True)
    geo_area = graphene.Field(ProjectGeoAreaType, required=True)
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum, required=True)

    def resolve_geo_area(root, info, **kwargs):
        return info.context.dl.assessment_registry.geo_area.load(root["geo_area"])


class MedianScoreOfGeoAreaAndAffectedGroupDateType(graphene.ObjectType):
    date = graphene.Date(required=True)
    final_score = graphene.Float(required=True)
    geo_area = graphene.Field(ProjectGeoAreaType, required=True)
    affected_group = graphene.Field(AssessmentRegistryAffectedGroupTypeEnum, required=True)

    def resolve_geo_area(root, info):
        return info.context.dl.assessment_registry.geo_area.load(root["geo_area"])


class MedianScoreOfSectorAndAffectedGroup(graphene.ObjectType):
    final_score = graphene.Float(required=True)
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum, required=True)
    affected_group = graphene.Field(AssessmentRegistryAffectedGroupTypeEnum, required=True)


class AssessmentDashboardStatisticsType(graphene.ObjectType):
    total_assessment = graphene.Int(required=True)
    total_stakeholder = graphene.Int(required=True)
    total_collection_technique = graphene.Int(required=True)
    assessment_count = graphene.List(graphene.NonNull(AssessmentCountType))
    stakeholder_count = graphene.List(graphene.NonNull(StakeholderCountType))
    collection_technique_count = graphene.List(graphene.NonNull(CollectionTechniqueCountType))
    total_multisector_assessment = graphene.Int(required=True)
    total_singlesector_assessment = graphene.Int(required=True)
    assessment_geographic_areas = graphene.List(graphene.NonNull(AssessmentDashboardGeographicalAreaType))
    assessment_by_over_time = graphene.List(graphene.NonNull(AssessmentCountByDateType))
    assessment_per_framework_pillar = graphene.List(graphene.NonNull(AssessmentFocusCountByDateType))
    assessment_per_affected_group = graphene.List(graphene.NonNull(AssessmentAffectedGroupCountByDateType))
    assessment_per_humanitarian_sector = graphene.List(graphene.NonNull(AssessmentHumanitrainSectorCountByDateType))
    assessment_per_protection_management = graphene.List(graphene.NonNull(AssessmentProtectionInformationCountByDateType))
    assessment_per_affected_group_and_sector = graphene.List(
        graphene.NonNull(AssessmentPerAffectedGroupAndSectorCountByDateType)
    )
    assessment_per_affected_group_and_geoarea = graphene.List(
        graphene.NonNull(AssessmentPerAffectedGroupAndGeoAreaCountByDateType)
    )
    assessment_per_sector_and_geoarea = graphene.List(graphene.NonNull(AssessmentPerSectorAndGeoAreaCountByDateType))
    assessment_by_lead_organization = graphene.List(graphene.NonNull(AssessmentByLeadOrganizationCountByDateType))
    assessment_per_datatechnique = graphene.List(graphene.NonNull(AssessmentPerDataCollectionTechniqueCountByDateType))
    assessment_per_unit_of_analysis = graphene.List(graphene.NonNull(AssessmentPerUnitofAnalysisCountByDateType))
    assessment_per_unit_of_reporting = graphene.List(graphene.NonNull(AssessmentPerUnitofReportingCountByDateType))
    assessment_per_sampling_approach = graphene.List(graphene.NonNull(AssessmentPerSamplingApproachCountByDateType))
    assessment_per_proximity = graphene.List(graphene.NonNull(AssessmentPerProximityCountByDateType))
    sample_size_per_data_collection_technique = graphene.List(
        graphene.NonNull(SamplingSizeAssessmentPerDataCollectionTechniqueCountByDateType)
    )
    assessment_by_data_collection_technique_and_geolocation = graphene.List(
        graphene.NonNull(AssessmentByGeographicalAndDataCollectionTechniqueCountByDateType)
    )
    assessment_by_sampling_approach_and_geolocation = graphene.List(
        graphene.NonNull(AssessmentByGeographicalAndSamplingApproachCountByDateType)
    )
    assessment_by_proximity_and_geolocation = graphene.List(
        graphene.NonNull(AssessmentByGeographicalAndProximityCountByDateType)
    )
    assessment_by_unit_of_analysis_and_geolocation = graphene.List(
        graphene.NonNull(AssessmentByGeographicalAndUnit_Of_AnalysisCountByDateType)
    )
    assessment_by_unit_of_reporting_and_geolocation = graphene.List(
        graphene.NonNull(AssessmentByGeographicalAndUnit_Of_ReportingCountByDateType)
    )
    median_quality_score_by_geo_area = graphene.List(graphene.NonNull(MedianQualityScoreByGeographicalAreaDateType))
    median_quality_score_over_time = graphene.List(graphene.NonNull(MedianQualityScoreOverTimeDateType))
    median_quality_score_over_time_by_month = graphene.List(graphene.NonNull(MedianQualityScoreOverTimeDateType))
    median_quality_score_of_each_dimension = graphene.List(graphene.NonNull(MedianScoreOfEachDimensionType))
    median_quality_score_of_each_dimension_by_date = graphene.List(graphene.NonNull(MedianScoreOfEachDimensionDateType))
    median_quality_score_of_each_dimension_by_date_month = graphene.List(
        graphene.NonNull(MedianScoreOfEachDimensionDateType))
    median_quality_score_of_analytical_density = graphene.List(graphene.NonNull(MedianScoreOfAnalyticalDensityType))
    median_quality_score_by_analytical_density_date = graphene.List(graphene.NonNull(MedianScoreOfAnalyticalDensityDateType))
    median_quality_score_by_analytical_density_date_month = graphene.List(
        graphene.NonNull(MedianScoreOfAnalyticalDensityDateType))
    median_quality_score_by_geoarea_and_sector = graphene.List(graphene.NonNull(MedianScoreOfGeographicalAndSectorDateType))
    median_quality_score_by_geoarea_and_sector_by_month = graphene.List(
        graphene.NonNull(MedianScoreOfGeographicalAndSectorDateType))
    median_quality_score_by_geoarea_and_affected_group = graphene.List(
        graphene.NonNull(MedianScoreOfGeoAreaAndAffectedGroupDateType)
    )
    median_score_by_sector_and_affected_group = graphene.List(graphene.NonNull(MedianScoreOfSectorAndAffectedGroup))
    median_score_by_sector_and_affected_group_by_month = graphene.List(graphene.NonNull(MedianScoreOfSectorAndAffectedGroup))

    @staticmethod
    def custom_resolver(root, info, _filter):
        assessment_qs = (
            AssessmentRegistry.objects.filter(
                project=info.context.active_project,
                **get_global_filters(_filter),
            )
        )
        assessment_qs_filter = AssessmentDashboardFilterSet(queryset=assessment_qs, data=_filter.get("assessment")).qs
        methodology_attribute_qs = MethodologyAttribute.objects.select_related("assessment_registry").filter(
            assessment_registry__in=assessment_qs_filter
        )
        cache_key = CacheHelper.generate_hash({
            'project': info.context.active_project.id,
            'filter': _filter.__dict__,
        })
        return AssessmentDashboardStat(
            cache_key=cache_key,
            assessment_registry_qs=assessment_qs_filter,
            methodology_attribute_qs=methodology_attribute_qs,
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.TOTAL_ASSESSMENT_COUNT)
    def resolve_total_assessment(root: AssessmentDashboardStat, info) -> int:
        return root.assessment_registry_qs.count()

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.TOTAL_STAKEHOLDER_COUNT)
    def resolve_total_stakeholder(root: AssessmentDashboardStat, info) -> int:
        qs = root.assessment_registry_qs.values("stakeholders").distinct()
        return qs.count()

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.TOTAL_COLLECTION_TECHNIQUE_COUNT)
    def resolve_total_collection_technique(root: AssessmentDashboardStat, info) -> int:
        return root.methodology_attribute_qs.values("data_collection_technique").distinct().count()

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_COUNT)
    def resolve_assessment_count(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.values("coordinated_joint")
            .annotate(count=Count("coordinated_joint"))
            .order_by("coordinated_joint")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.STAKEHOLDER_COUNT)
    def resolve_stakeholder_count(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.filter(stakeholders__organization_type__title__isnull=False)
            .values(stakeholder=models.F('stakeholders__organization_type__title'))
            .annotate(count=Count('id'))
            .order_by('stakeholder')
            .values('count', 'stakeholder')
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.COLLECTION_TECHNIQUE_COUNT)
    def resolve_collection_technique_count(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values("data_collection_technique")
            .annotate(count=Count("data_collection_technique"))
            .order_by("data_collection_technique")
            .values('data_collection_technique', 'count')
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.TOTAL_MULTISECTOR_ASSESSMENT_COUNT)
    def resolve_total_multisector_assessment(root: AssessmentDashboardStat, info) -> int:
        return root.assessment_registry_qs.filter(sectors__len__gte=2).count()

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.TOTAL_SINGLESECTOR_ASSESSMENT_COUNT)
    def resolve_total_singlesector_assessment(root: AssessmentDashboardStat, info) -> int:
        return root.assessment_registry_qs.filter(sectors__len=1).count()

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_BY_GEOAREA)
    def resolve_assessment_geographic_areas(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.filter(locations__isnull=False).values("locations")
            .annotate(
                region=models.F("locations__admin_level__region"),
                count=Count("locations__id"),
                assessment_ids=ArrayAgg("id"),
                geo_area=models.F("locations__id"),
                admin_level_id=models.F("locations__admin_level_id"),
                code=models.F("locations__code"),
            )
            .values(
                'locations',
                'count',
                'assessment_ids',
                'geo_area',
                'admin_level_id',
                'code',
                'region',
            )
            .order_by("locations")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.OVER_THE_TIME)
    def resolve_assessment_by_over_time(root: AssessmentDashboardStat, info):
        return count_by_date_queryset_generator(root.assessment_registry_qs, TruncDay)

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_PER_FRAMEWORK_PILLAR)
    def resolve_assessment_per_framework_pillar(root: AssessmentDashboardStat, info):
        return root.assessment_registry_qs.annotate(
            focus=models.Func(models.F("focuses"), function="unnest"),
        ).values('focus').order_by('focus').annotate(
            count=Count('id')
        ).values('focus', 'count').annotate(
            date=TruncDay('created_at')
        ).values('focus', 'count', 'date')

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_PER_AFFECTED_GROUP)
    def resolve_assessment_per_affected_group(root: AssessmentDashboardStat, info):
        return root.assessment_registry_qs.annotate(
            affected_group=models.Func(models.F('affected_groups'), function='unnest'),
        ).values('affected_group').order_by('affected_group').annotate(
            count=Count('id')
        ).values('affected_group', 'count').annotate(
            date=TruncDay('created_at')
        ).values('affected_group', 'count', 'date')

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_PER_HUMANITRATION_SECTOR)
    def resolve_assessment_per_humanitarian_sector(root: AssessmentDashboardStat, info):
        return root.assessment_registry_qs.annotate(
            sector=models.Func(models.F('sectors'), function='unnest'),
        ).values('sector').order_by('sector').annotate(
            count=Count('id')
        ).values('sector', 'count').annotate(
            date=TruncDay('created_at')
        ).values('sector', 'count', 'date')

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_PER_PROTECTION_MANAGEMENT)
    def resolve_assessment_per_protection_management(root: AssessmentDashboardStat, info):
        return root.assessment_registry_qs.annotate(
            protection_management=models.Func(models.F('protection_info_mgmts'), function='unnest'),
        ).values('protection_management').order_by('protection_management').annotate(
            count=Count('id')
        ).values('protection_management', 'count').annotate(
            date=TruncDay('created_at')
        ).values('protection_management', 'count', 'date')

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_AFFECTED_GROUP_AND_SECTOR)
    def resolve_assessment_per_affected_group_and_sector(root: AssessmentDashboardStat, info):
        # TODO : Global filter and assessment filter need to implement
        with django_db_connection.cursor() as cursor:
            query = f'''
                SELECT
                    sector,
                    affected_group,
                    Count(*) as count
                FROM (
                    select
                        -- Only select required fields
                        id,
                        sectors,
                        affected_groups,
                        project_id
                FROM assessment_registry_assessmentregistry
                    -- Only process required rows
                )as t
                CROSS JOIN unnest(t.sectors) AS sector
                CROSS JOIN unnest(t.affected_groups) AS affected_group
                WHERE project_id = {info.context.active_project.id}
                GROUP BY sector, affected_group
                ORDER BY sector, affected_group DESC;
                '''
            cursor.execute(query, {})
            return [
                AssessmentPerAffectedGroupAndSectorCountByDateType(sector=data[0], affected_group=data[1], count=data[2])
                for data in cursor.fetchall()
            ]

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_AFFECTED_GROUP_AND_GEOAREA)
    def resolve_assessment_per_affected_group_and_geoarea(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.values("locations", date=TruncDay("created_at"))
            .annotate(
                geo_area=models.F("locations"),
                count=Count("id"),
                affected_group=models.Func(models.F("affected_groups"), function="unnest"),
            )
            .filter(locations__admin_level__level=1)
            .values("geo_area", "affected_group", "count", "date")
            .order_by("-count")[:10]
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_SECTOR_AND_GEOAREA)
    def resolve_assessment_per_sector_and_geoarea(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.values("locations")
            .annotate(
                geo_area=models.F("locations"),
                count=Count("id"),
                sector=models.Func(models.F("sectors"), function="unnest"),
            )
            .filter(locations__admin_level__level=1)
            .values("geo_area", "sector", "count")
            .order_by("-count")[:10]
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_BY_LEAD_ORGANIZATION)
    def resolve_assessment_by_lead_organization(root: AssessmentDashboardStat, info):
        return (
            AssessmentRegistryOrganization.objects.filter(
                organization_type=AssessmentRegistryOrganization.Type.LEAD_ORGANIZATION
            )
            .values(date=TruncDay("assessment_registry__created_at"))
            .filter(assessment_registry__in=root.assessment_registry_qs)
            .annotate(count=Count("organization"))
            .values("organization", "count", "date")
            .order_by("-count")[:10]
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_PER_DATA_COLLECTION_TECHNIQUE)
    def resolve_assessment_per_datatechnique(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(count=Count("data_collection_technique"))
            .values("data_collection_technique", "count", "date")
            .order_by("data_collection_technique")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_PER_UNIT_ANALYSIS)
    def resolve_assessment_per_unit_of_analysis(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(count=Count("unit_of_analysis"))
            .values("unit_of_analysis", "count", "date")
            .order_by("unit_of_analysis")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_PER_UNIT_REPORTING)
    def resolve_assessment_per_unit_of_reporting(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(count=Count("unit_of_reporting"))
            .values("unit_of_reporting", "count", "date")
            .order_by("unit_of_reporting")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_PER_SAMPLE_APPROACH)
    def resolve_assessment_per_sampling_approach(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(count=Count("sampling_approach"))
            .values("sampling_approach", "count", "date")
            .order_by("sampling_approach")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.ASSESSMENT_PER_PROXIMITY)
    def resolve_assessment_per_proximity(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(count=Count("proximity"))
            .values("proximity", "count", "date")
            .order_by("proximity")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.SAMPLE_SIZE_PER_DATA_COLLECTION_TECHNIQUE)
    def resolve_sample_size_per_data_collection_technique(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.values(date=TruncDay("assessment_registry__created_at"))
            .annotate(sampling_size=Sum("sampling_size"))
            .values("sampling_size", "data_collection_technique", "date")
            .order_by("data_collection_technique")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.DATA_COLLECTION_TECHNIQUE_AND_GEOLOCATION)
    def resolve_assessment_by_data_collection_technique_and_geolocation(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.filter(assessment_registry__locations__isnull=False)
            .values(
                "data_collection_technique",
                geo_area=models.F("assessment_registry__locations"),
                region=models.F("assessment_registry__locations__admin_level__region"),
                admin_level_id=models.F("assessment_registry__locations__admin_level_id"),
            )
            .annotate(count=Count("assessment_registry__locations"))
            .values('data_collection_technique', 'geo_area', 'region', 'admin_level_id', 'count')
            .order_by("assessment_registry__locations")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.SAMPLING_APPROACH_AND_GEOLOCATION)
    def resolve_assessment_by_sampling_approach_and_geolocation(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.filter(assessment_registry__locations__isnull=False)
            .values(
                "sampling_approach",
                geo_area=models.F("assessment_registry__locations"),
                region=models.F("assessment_registry__locations__admin_level__region"),
                admin_level_id=models.F("assessment_registry__locations__admin_level_id"),
            )
            .annotate(count=Count("assessment_registry__locations"))
            .values('sampling_approach', 'geo_area', 'region', 'admin_level_id', 'count')
            .order_by("assessment_registry__locations")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.PROXIMITY_AND_GEOLOCATION)
    def resolve_assessment_by_proximity_and_geolocation(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.filter(assessment_registry__locations__isnull=False)
            .values(
                "proximity",
                geo_area=models.F("assessment_registry__locations"),
                region=models.F("assessment_registry__locations__admin_level__region"),
                admin_level_id=models.F("assessment_registry__locations__admin_level_id"),
            )
            .annotate(count=Count("assessment_registry__locations"))
            .values('proximity', 'geo_area', 'region', 'admin_level_id', 'count')
            .order_by("assessment_registry__locations")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.UNIT_OF_ANALYSIS_AND_GEOLOCATION)
    def resolve_assessment_by_unit_of_analysis_and_geolocation(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.filter(assessment_registry__locations__isnull=False).values(
                "unit_of_analysis",
                geo_area=models.F("assessment_registry__locations"),
                region=models.F("assessment_registry__locations__admin_level__region"),
                admin_level_id=models.F("assessment_registry__locations__admin_level_id"),
            )
            .annotate(count=Count("assessment_registry__locations"))
            .values('geo_area', 'region', 'admin_level_id', 'unit_of_analysis', 'count')
            .order_by("assessment_registry__locations")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.UNIT_REPORTING_AND_GEOLOCATION)
    def resolve_assessment_by_unit_of_reporting_and_geolocation(root: AssessmentDashboardStat, info):
        return (
            root.methodology_attribute_qs.filter(assessment_registry__locations__isnull=False).values(
                "unit_of_reporting",
                geo_area=models.F("assessment_registry__locations"),
                region=models.F("assessment_registry__locations__admin_level__region"),
                admin_level_id=models.F("assessment_registry__locations__admin_level_id"),
            )
            .annotate(count=Count("assessment_registry__locations"))
            .values('unit_of_reporting', 'count', 'geo_area', 'region', 'admin_level_id')
            .order_by("assessment_registry__locations")
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_BY_GEO_AREA)
    def resolve_median_quality_score_by_geo_area(root: AssessmentDashboardStat, info):
        # TODO final score value should be convert into  functions
        score = (
            root.assessment_registry_qs.annotate(geo_area=models.F("locations"))
            .annotate(
                score_rating_matrix=(
                    Sum(
                        Case(
                            When(score_ratings__rating=1, then=(Value(0))),
                            When(score_ratings__rating=2, then=(Value(0.5))),
                            When(score_ratings__rating=3, then=(Value(1))),
                            When(score_ratings__rating=4, then=(Value(1.5))),
                            When(score_ratings__rating=5, then=(Value(2))),
                            output_field=models.FloatField(),
                        )
                    )
                )
            )
            .values("geo_area")
            .order_by()
            .annotate(
                final_score=(
                    Avg(
                        (
                            models.F("analytical_density__figure_provided__len") *
                            models.F("analytical_density__analysis_level_covered__len")
                        ) / models.Value(10)
                    ) + (models.F("score_rating_matrix"))
                ) / Count("id") * 5
            )
            .order_by()
            .values(
                "final_score",
                "geo_area",
                region=models.F("locations__admin_level__region"),
                admin_level_id=models.F("locations__admin_level_id"),
            )
        ).exclude(final_score__isnull=True)
        return score

    # per day data of median_quality_score_over_time
    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_OVER_TIME)
    def resolve_median_quality_score_over_time(root: AssessmentDashboardStat, info):
        # TODO final score value should be convert into  functions
        score = (
            root.assessment_registry_qs.annotate(date=TruncDay("created_at"))
            .annotate(
                score_rating_matrix=(
                    Case(
                        When(score_ratings__rating=1, then=(Value(0))),
                        When(score_ratings__rating=2, then=(Value(0.5))),
                        When(score_ratings__rating=3, then=(Value(1))),
                        When(score_ratings__rating=4, then=(Value(1.5))),
                        When(score_ratings__rating=4, then=(Value(2))),
                        output_field=models.FloatField(),
                    )
                )
            )
            .values("date")
            .order_by()
            .annotate(
                final_score=(
                    Avg(
                        (
                            models.F("analytical_density__figure_provided__len") *
                            models.F("analytical_density__analysis_level_covered__len")
                        ) / models.Value(10)
                    ) + Sum(models.F("score_rating_matrix"))
                ) / Count("id") * 5
            )
            .values("final_score", "date")
        ).exclude(final_score__isnull=True)
        return score

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_OVER_TIME_BY_MONTH)
    def resolve_median_quality_score_over_time_by_month(root: AssessmentDashboardStat, info):
        # TODO final score value should be convert into  functions
        score = (
            root.assessment_registry_qs.annotate(date=TruncMonth("created_at"))
            .annotate(
                score_rating_matrix=(
                    Case(
                        When(score_ratings__rating=1, then=(Value(0))),
                        When(score_ratings__rating=2, then=(Value(0.5))),
                        When(score_ratings__rating=3, then=(Value(1))),
                        When(score_ratings__rating=4, then=(Value(1.5))),
                        When(score_ratings__rating=4, then=(Value(2))),
                        output_field=models.FloatField(),
                    )
                )
            )
            .values("date")
            .order_by()
            .annotate(
                final_score=(
                    Avg(
                        (
                            models.F("analytical_density__figure_provided__len") *
                            models.F("analytical_density__analysis_level_covered__len")
                        ) / models.Value(10)
                    ) + Sum(models.F("score_rating_matrix"))
                ) / Count("id") * 5
            )
            .values("final_score", "date")
        ).exclude(final_score__isnull=True)
        return score

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_OF_EACH_DIMENSION)
    def resolve_median_quality_score_of_each_dimension(root: AssessmentDashboardStat, info):
        # TODO final score value should be convert into  functions
        return (
            root.assessment_registry_qs.annotate(
                score_rating_matrix=(
                    Case(
                        When(score_ratings__rating=1, then=(Value(0))),
                        When(score_ratings__rating=2, then=(Value(0.5))),
                        When(score_ratings__rating=3, then=(Value(1))),
                        When(score_ratings__rating=4, then=(Value(1.5))),
                        When(score_ratings__rating=4, then=(Value(2))),
                        output_field=models.FloatField(),
                    )
                )
            )
            .annotate(final_score=Sum("score_rating_matrix"))
            .values("final_score", score_type=models.F("score_ratings__score_type"))
            .exclude(final_score__isnull=True)
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_OF_EACH_DIMENSION_BY_DATE)
    def resolve_median_quality_score_of_each_dimension_by_date(root: AssessmentDashboardStat, info):
        # TODO final score value should be convert into  functions
        return (
            root.assessment_registry_qs.values(date=TruncDay("created_at"))
            .annotate(
                score_rating_matrix=(
                    Case(
                        When(score_ratings__rating=1, then=(Value(0))),
                        When(score_ratings__rating=2, then=(Value(0.5))),
                        When(score_ratings__rating=3, then=(Value(1))),
                        When(score_ratings__rating=4, then=(Value(1.5))),
                        When(score_ratings__rating=4, then=(Value(2))),
                        output_field=models.FloatField(),
                    )
                )
            )
            .values("date")
            .annotate(final_score=Sum("score_rating_matrix"))
            .values("final_score", "date", score_type=models.F("score_ratings__score_type"))
            .exclude(final_score__isnull=True)
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_OF_EACH_DIMENSION_BY_DATE_MONTH)
    def resolve_median_quality_score_of_each_dimension_by_date_month(root: AssessmentDashboardStat, info):
        # TODO final score value should be convert into  functions
        return (
            root.assessment_registry_qs.values(date=TruncMonth("created_at"))
            .annotate(
                score_rating_matrix=(
                    Case(
                        When(score_ratings__rating=1, then=(Value(0))),
                        When(score_ratings__rating=2, then=(Value(0.5))),
                        When(score_ratings__rating=3, then=(Value(1))),
                        When(score_ratings__rating=4, then=(Value(1.5))),
                        When(score_ratings__rating=4, then=(Value(2))),
                        output_field=models.FloatField(),
                    )
                )
            )
            .values("date")
            .annotate(final_score=Sum("score_rating_matrix"))
            .values("final_score", "date", score_type=models.F("score_ratings__score_type"))
            .exclude(final_score__isnull=True)
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_OF_ANALYTICAL_DENSITY)
    def resolve_median_quality_score_of_analytical_density(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.values("analytical_density__sector")
            .annotate(
                final_score=(
                    Avg(
                        models.F("analytical_density__figure_provided__len") *
                        models.F("analytical_density__analysis_level_covered__len")
                    )
                ) / models.Value(10)
            )
            .order_by()
            .values("final_score", sector=models.F("analytical_density__sector"))
            .exclude(analytical_density__sector__isnull=True)
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_BY_ANALYTICAL_DENSITY_DATE)
    def resolve_median_quality_score_by_analytical_density_date(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.values(date=TruncDay("created_at"))
            .annotate(
                final_score=(
                    Avg(
                        models.F("analytical_density__figure_provided__len") *
                        models.F("analytical_density__analysis_level_covered__len")
                    )
                ) / models.Value(10)
            )
            .values("final_score", "date", sector=models.F("analytical_density__sector"))
            .exclude(analytical_density__sector__isnull=True)
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_BY_ANALYTICAL_DENSITY_DATE_MONTH)
    def resolve_median_quality_score_by_analytical_density_date_month(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.values(date=TruncMonth("created_at"))
            .annotate(
                final_score=(
                    Avg(
                        models.F("analytical_density__figure_provided__len") *
                        models.F("analytical_density__analysis_level_covered__len")
                    )
                ) / models.Value(10)
            )
            .values("final_score", "date", sector=models.F("analytical_density__sector"))
            .exclude(analytical_density__sector__isnull=True)
        )

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_BY_GEOAREA_AND_SECTOR)
    def resolve_median_quality_score_by_geoarea_and_sector(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.filter(locations__admin_level__level=1)
            .values(
                "locations",
                date=TruncDay("created_at"),
            )
            .annotate(
                final_score=(
                    Avg(
                        models.F("analytical_density__figure_provided__len") *
                        models.F("analytical_density__analysis_level_covered__len")
                    )
                ) / models.Value(10)
            )
            .annotate(geo_area=models.F("locations"), sector=models.F("analytical_density__sector"))
            .values("geo_area", "final_score", "sector", "date")
        ).exclude(analytical_density__sector__isnull=True, analytical_density__analysis_level_covered__isnull=True)

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_BY_GEOAREA_AND_SECTOR_BY_MONTH)
    def resolve_median_quality_score_by_geoarea_and_sector_by_month(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.filter(locations__admin_level__level=1)
            .values(
                "locations",
                date=TruncMonth("created_at"),
            )
            .annotate(
                final_score=(
                    Avg(
                        models.F("analytical_density__figure_provided__len") *
                        models.F("analytical_density__analysis_level_covered__len")
                    )
                ) / models.Value(10)
            )
            .annotate(geo_area=models.F("locations"), sector=models.F("analytical_density__sector"))
            .values("geo_area", "final_score", "sector", "date")
        ).exclude(analytical_density__sector__isnull=True, analytical_density__analysis_level_covered__isnull=True)

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_BY_GEOAREA_AND_AFFECTED_GROUP)
    def resolve_median_quality_score_by_geoarea_and_affected_group(root: AssessmentDashboardStat, info):
        score = (
            root.assessment_registry_qs.filter(locations__admin_level_id=1)
            .values("locations", date=TruncDay("created_at"))
            .annotate(
                score_rating_matrix=(
                    Case(
                        When(score_ratings__rating=1, then=(Value(0))),
                        When(score_ratings__rating=2, then=(Value(0.5))),
                        When(score_ratings__rating=3, then=(Value(1))),
                        When(score_ratings__rating=4, then=(Value(1.5))),
                        When(score_ratings__rating=5, then=(Value(2))),
                        output_field=models.FloatField(),
                    )
                )
            )
            .values("date")
            .annotate(
                final_score=(
                    Avg(
                        (
                            models.F("analytical_density__figure_provided__len") *
                            models.F("analytical_density__analysis_level_covered__len")
                        ) / models.Value(10)
                    ) + Sum(models.F("score_rating_matrix"))
                ) / Count("id") * 5,
            )
            .annotate(affected_group=models.Func(models.F("affected_groups"), function="unnest"))
            .values("final_score", "date", "affected_group", geo_area=models.F("locations"))
        ).exclude(final_score__isnull=True)

        return score

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_QUALITY_SCORE_BY_GEOAREA_AND_SECTOR_BY_MONTH)
    def resolve_median_quality_score_by_geoarea_and_affected_group_by_month(root: AssessmentDashboardStat, info):
        score = (
            root.assessment_registry_qs.filter(locations__admin_level_id=1)
            .values("locations", date=TruncMonth("created_at"))
            .annotate(
                score_rating_matrix=(
                    Case(
                        When(score_ratings__rating=1, then=(Value(0))),
                        When(score_ratings__rating=2, then=(Value(0.5))),
                        When(score_ratings__rating=3, then=(Value(1))),
                        When(score_ratings__rating=4, then=(Value(1.5))),
                        When(score_ratings__rating=5, then=(Value(2))),
                        output_field=models.FloatField(),
                    )
                )
            )
            .values("date")
            .annotate(
                final_score=(
                    Avg(
                        (
                            models.F("analytical_density__figure_provided__len") *
                            models.F("analytical_density__analysis_level_covered__len")
                        ) / models.Value(10)
                    ) + Sum(models.F("score_rating_matrix"))
                ) / Count("id") * 5,
            )
            .annotate(affected_group=models.Func(models.F("affected_groups"), function="unnest"))
            .values("final_score", "date", "affected_group", geo_area=models.F("locations"))
        ).exclude(final_score__isnull=True)

        return score

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_SCORE_BY_SECTOR_AND_AFFECTED_GROUP)
    def resolve_median_score_by_sector_and_affected_group(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.values(
                date=TruncDay("created_at"),
            )
            .annotate(
                final_score=(
                    Avg(
                        models.F("analytical_density__figure_provided__len") *
                        models.F("analytical_density__analysis_level_covered__len")
                    )
                ) / models.Value(10)
            )
            .annotate(
                affected_group=models.Func(models.F("affected_groups"), function="unnest"),
                sector=models.F("analytical_density__sector"),
            )
            .values("affected_group", "final_score", "sector", "date")
        ).exclude(analytical_density__sector__isnull=True, analytical_density__analysis_level_covered__isnull=True)

    @staticmethod
    @node_cache(CacheKey.AssessmentDashboard.MEDIAN_SCORE_BY_SECTOR_AND_AFFECTED_GROUP_BY_MONTH)
    def resolve_median_score_by_sector_and_affected_group_by_month(root: AssessmentDashboardStat, info):
        return (
            root.assessment_registry_qs.values(
                date=TruncMonth("created_at"),
            )
            .annotate(
                final_score=(
                    Avg(
                        models.F("analytical_density__figure_provided__len") *
                        models.F("analytical_density__analysis_level_covered__len")
                    )
                ) / models.Value(10)
            )
            .annotate(
                affected_group=models.Func(models.F("affected_groups"), function="unnest"),
                sector=models.F("analytical_density__sector"),
            )
            .values("affected_group", "final_score", "sector", "date")
        ).exclude(analytical_density__sector__isnull=True, analytical_density__analysis_level_covered__isnull=True)


class Query:
    assessment_dashboard_statistics = graphene.Field(
        AssessmentDashboardStatisticsType,
        filter=AssessmentDashboardFilterInputType(required=True),
    )

    @staticmethod
    def resolve_assessment_dashboard_statistics(root, info, filter):
        return AssessmentDashboardStatisticsType.custom_resolver(root, info, filter)
