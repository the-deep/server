import typing

from django.test import override_settings
from django.core.files.base import ContentFile

from utils.files import generate_json_file_for_upload


class SnapshotQuery:
    class DeepExplore:
        YEARLY = """
            query MyQuery($filter: ExploreDeepFilterInputType!) {
              deepExploreStats(filter: $filter) {
                totalActiveUsers
                totalAuthors
                totalEntries
                totalEntriesAddedLastWeek
                totalLeads
                totalProjects
                totalPublishers
                totalRegisteredUsers
                topTenPublishers {
                  id
                  title
                  leadsCount
                  projectsCount
                }
                topTenProjectsByUsers {
                  id
                  title
                  usersCount
                }
                topTenProjectsByEntries {
                  id
                  title
                  entriesCount
                  leadsCount
                }
                topTenProjectsByLeads {
                  id
                  title
                  entriesCount
                  leadsCount
                }
                topTenFrameworks {
                  id
                  title
                  projectsCount
                  entriesCount
                }
                topTenAuthors {
                  id
                  title
                  projectsCount
                  leadsCount
                }
                projectsByRegion {
                  id
                  centroid
                  projectIds
                }
                entriesCountByRegion {
                  centroid
                  count
                }
              }
            }
        """

        GLOBAL_TIME_SERIES = """
            query MyQuery($filter: ExploreDeepFilterInputType!) {
              deepExploreStats(filter: $filter) {
                projectsCountByMonth {
                  count
                  date
                }
                projectsCountByDay {
                  count
                  date
                }
                leadsCountByMonth {
                  date
                  count
                }
                leadsCountByDay {
                  date
                  count
                }
                entriesCountByMonth {
                  date
                  count
                }
                entriesCountByDay {
                  date
                  count
                }
              }
            }
        """

        GLOBAL_FULL = """
            query MyQuery($filter: ExploreDeepFilterInputType!) {
              deepExploreStats(filter: $filter) {
                totalActiveUsers
                totalAuthors
                totalEntries
                totalEntriesAddedLastWeek
                totalLeads
                totalProjects
                totalPublishers
                totalRegisteredUsers
                topTenPublishers {
                  id
                  title
                  leadsCount
                  projectsCount
                }
                topTenProjectsByUsers {
                  id
                  title
                  usersCount
                }
                topTenProjectsByEntries {
                  id
                  title
                  entriesCount
                  leadsCount
                }
                topTenProjectsByLeads {
                  id
                  title
                  entriesCount
                  leadsCount
                }
                topTenFrameworks {
                  id
                  title
                  projectsCount
                  entriesCount
                }
                topTenAuthors {
                  id
                  title
                  projectsCount
                  leadsCount
                }
                projectsByRegion {
                  id
                  centroid
                  projectIds
                }
                entriesCountByRegion {
                  centroid
                  count
                }
                projectsCountByMonth {
                  count
                  date
                }
                projectsCountByDay {
                  count
                  date
                }
                leadsCountByMonth {
                  date
                  count
                }
                leadsCountByDay {
                  date
                  count
                }
                entriesCountByMonth {
                  date
                  count
                }
                entriesCountByDay {
                  date
                  count
                }
              }
            }
        """

    class AnalysisReport:
        SnapshotFragment = '''
            fragment OrganizationGeneralResponse on OrganizationType {
                id
                title
                verified
                shortName
                logo {
                    id
                }
                mergedAs {
                    id
                    title
                    shortName
                    logo {
                        id
                    }
                }
            }
            fragment GridLineStyle on AnalysisReportGridLineStyleType {
                lineColor
                lineOpacity
                lineWidth
            }
            fragment TickStyle on AnalysisReportTickStyleType {
                lineColor
                lineOpacity
                lineWidth
            }
            fragment TextStyle on AnalysisReportTextStyleType {
                align
                color
                family
                size
                weight
            }
            fragment PaddingStyle on AnalysisReportPaddingStyleType {
                top
                bottom
                right
                left
            }
            fragment BorderStyle on AnalysisReportBorderStyleType {
                color
                opacity
                style
                width
            }
            fragment AnalysisReportQueryType on AnalysisReportType {
                id
                analysis
                title
                subTitle
                slug
                organizations {
                    ...OrganizationGeneralResponse
                }
                configuration {
                    containerStyle {
                        border {
                            ...BorderStyle
                        }
                        padding {
                            ...PaddingStyle
                        }
                        background {
                            color
                            opacity
                        }
                    }
                    textContentStyle {
                        content {
                            ...TextStyle
                        }
                    }
                    imageContentStyle {
                        caption {
                            ...TextStyle
                        }
                    }
                    headingContentStyle {
                        h1 {
                            ...TextStyle
                        }
                        h2 {
                            ...TextStyle
                        }
                        h3 {
                            ...TextStyle
                        }
                        h4 {
                            ...TextStyle
                        }
                    }
                    bodyStyle {
                        gap
                    }
                }
                containers {
                    id
                    clientId
                    row
                    column
                    width
                    height
                    contentType
                    style {
                        border {
                            ...BorderStyle
                        }
                        padding {
                            ...PaddingStyle
                        }
                        background {
                            color
                            opacity
                        }
                    }
                    contentData {
                        clientId
                        data
                        id
                        upload {
                            id
                            file {
                                id
                            }
                            type
                            metadata {
                                csv {
                                    headerRow
                                    variables {
                                        clientId
                                        completeness
                                        name
                                        type
                                    }
                                }
                                xlsx {
                                    sheets {
                                        clientId
                                        headerRow
                                        name
                                        variables {
                                            clientId
                                            completeness
                                            name
                                            type
                                        }
                                    }
                                }
                            }
                        }
                    }
                    contentConfiguration {
                        heading {
                            content
                            variant
                            style {
                                content {
                                    ...TextStyle
                                }
                            }
                        }
                        image {
                            altText
                            caption
                            style {
                                caption {
                                    ...TextStyle
                                }
                                fit
                            }
                        }
                        text {
                            content
                            style {
                                content {
                                    ...TextStyle
                                }
                            }
                        }
                        kpi {
                            items {
                                abbreviateValue
                                clientId
                                color
                                date
                                source
                                sourceUrl
                                subtitle
                                title
                                value
                            }
                            sourceContentStyle {
                                content {
                                    ...TextStyle
                                }
                            }
                            subtitleContentStyle {
                                content {
                                    ...TextStyle
                                }
                            }
                            titleContentStyle {
                                content {
                                    ...TextStyle
                                }
                            }
                            valueContentStyle {
                                content {
                                    ...TextStyle
                                }
                            }
                        }
                        barChart {
                            direction
                            horizontalAxis {
                                field
                                type
                            }
                            horizontalAxisLineVisible
                            horizontalAxisTitle
                            horizontalGridLineVisible
                            horizontalTickVisible
                            legendHeading
                            sheet
                            subTitle
                            title
                            type
                            verticalAxis {
                                label
                                aggregationType
                                clientId
                                color
                                field
                            }
                            verticalAxisExtendMinimumValue
                            verticalAxisExtendMaximumValue
                            verticalAxisLineVisible
                            verticalAxisTitle
                            verticalGridLineVisible
                            verticalTickVisible
                            horizontalTickLabelRotation
                            style {
                                bar {
                                    border {
                                        ...BorderStyle
                                    }
                                }
                                horizontalAxisTickLabel {
                                    ...TextStyle
                                }
                                horizontalAxisTitle {
                                    ...TextStyle
                                }
                                horizontalGridLine {
                                    ...GridLineStyle
                                }
                                horizontalTick {
                                    ...TickStyle
                                }
                                legend {
                                    heading {
                                        ...TextStyle
                                    }
                                    label {
                                        ...TextStyle
                                    }
                                    position
                                    shape
                                }
                                subTitle {
                                    ...TextStyle
                                }
                                title {
                                    ...TextStyle
                                }
                                verticalAxisTickLabel {
                                    ...TextStyle
                                }
                                verticalAxisTitle {
                                    ...TextStyle
                                }
                                verticalGridLine {
                                    ...GridLineStyle
                                }
                                verticalTick {
                                    ...TickStyle
                                }
                            }
                        }
                        timelineChart {
                            category
                            date
                            detail
                            sheet
                            source
                            sourceUrl
                            title
                        }
                        url {
                            url
                        }
                    }
                }
            }
        '''
        Snapshot = (
            SnapshotFragment +
            '''\n
            query MyQuery($projectID: ID!, $reportID: ID!) {
                project(id: $projectID) {
                    analysisReport(id: $reportID) {
                        ...AnalysisReportQueryType
                    }
                }
            }
            '''
        )


class DummyContext:
    request = None


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    },
)
def generate_query_snapshot(
    query: str,
    variables: dict,
    data_callback: typing.Callable = lambda x: x,
    context: typing.Optional[object] = None,
) -> \
        typing.Tuple[typing.Optional[ContentFile], typing.Optional[dict]]:
    # To avoid circular dependency
    from deep.schema import schema as gql_schema
    if context is None:
        context = DummyContext()
    result = gql_schema.execute(
        query,
        context=context,
        variables=variables
    )
    if result.errors:
        return None, result.errors
    return generate_json_file_for_upload(data_callback(result.data)), None
