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
