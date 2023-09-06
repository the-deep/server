import typing
import graphene

from .schema import AnalysisReportSnapshotType
from .models import AnalysisReport, AnalysisReportSnapshot


class Query:
    public_analysis_report_snapshot = graphene.Field(
        AnalysisReportSnapshotType,
        slug=graphene.String(required=True),
    )

    @staticmethod
    def resolve_analysis_report_snapshot(root, info, slug, **kwargs) -> typing.Optional[AnalysisReportSnapshot]:
        return AnalysisReport.get_latest_snapshot(slug=slug)
