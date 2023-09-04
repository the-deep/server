import typing
import graphene

from .schema import AnalysisReportSnapshotType
from .models import AnalysisReportSnapshot


class Query:
    public_analysis_report_snapshot = graphene.Field(
        AnalysisReportSnapshotType,
        slug=graphene.String(required=True),
    )

    @staticmethod
    def resolve_analysis_report_snapshot(root, info, slug, **kwargs) -> typing.Optional[AnalysisReportSnapshot]:
        return AnalysisReportSnapshot.objects.filter(
            report__is_public=True,
            report__slug=slug,
        ).order_by('-published_on').first()
