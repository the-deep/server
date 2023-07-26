import graphene
from .models import AssessmentRegistry, MethodologyAttribute
from .enums import (
    AssessmentRegistryCoordinationTypeEnum,
    AssessmentRegistryDataCollectionTechniqueTypeEnum,
)
from django.db.models import Count


class AssessmentCount(graphene.ObjectType):
    coordinated_joint = graphene.Field(AssessmentRegistryCoordinationTypeEnum)
    coordinated_joint_display = graphene.String()
    count = graphene.Int()

    def resolve_coordinated_joint_display(self, info):
        return AssessmentRegistry.CoordinationType(self.coordinated_joint).label


class StakeholderCount(graphene.ObjectType):
    stakeholder = graphene.String()
    count = graphene.Int()


class CollectionTechniqueCount(graphene.ObjectType):
    data_collection_technique = graphene.Field(
        AssessmentRegistryDataCollectionTechniqueTypeEnum
    )
    data_collection_technique_display = graphene.String()
    count = graphene.Int()

    def resolve_data_collection_technique_display(self, info):
        return MethodologyAttribute.CollectionTechniqueType(
            self.data_collection_technique
        ).label


class AssessmentDashboardStatistics(graphene.ObjectType):
    assessment_count = graphene.List(AssessmentCount)
    stakeholder_count = graphene.List(StakeholderCount)
    collection_technique_count = graphene.List(CollectionTechniqueCount)
    model = AssessmentRegistry

    def resolve_assessment_count(self, info):
        assessment = (
            self.model.objects.filter(project=info.context.active_project)
            .values("coordinated_joint")
            .annotate(count=Count("coordinated_joint"))
            .order_by("coordinated_joint")
        )
        return [
            AssessmentCount(
                coordinated_joint=assessment["coordinated_joint"],
                count=assessment["count"],
            )
            for assessment in assessment
        ]

    def resolve_stakeholder_count(self, info):
        stakeholder = (
            self.model.objects.filter(project=info.context.active_project)
            .values("lead_organizations", "lead_organizations__title")
            .annotate(count=Count("lead_organizations"))
            .order_by("lead_organizations")
        )
        return [
            StakeholderCount(
                stakeholder=stakeholder["lead_organizations__title"],
                count=stakeholder["count"],
            )
            for stakeholder in stakeholder
        ]

    def resolve_collection_technique_count(self, info):
        data_collection_technique = (
            MethodologyAttribute.objects.filter(
                assessment_registry__project_id=info.context.active_project
            )
            .values("data_collection_technique")
            .annotate(count=Count("data_collection_technique"))
            .order_by("data_collection_technique")
        )
        return [
            CollectionTechniqueCount(
                data_collection_technique=technique["data_collection_technique"],
                count=technique["count"],
            )
            for technique in data_collection_technique
        ]


class Query:
    assessment_dashboard_statistics = graphene.Field(
        AssessmentDashboardStatistics)

    @staticmethod
    def resolve_assessment_dashboard_statistics(root, info, **kwargs):
        return AssessmentDashboardStatistics
