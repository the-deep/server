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
        Snapshot = '''
            query MyQuery($projectID: ID!, $reportID: ID!) {
              project(id: $projectID) {
                analysisReport(id: $reportID) {
                  id
                  analysis
                  isPublic
                  slug
                  subTitle
                  title
                  organizations {
                    id
                    title
                    shortName
                    mergedAs {
                      id
                      title
                      shortName
                      longName
                    }
                  }
                  configuration {
                    bodyStyle {
                      gap
                    }
                    containerStyle {
                      background {
                        color
                        opacity
                      }
                      border {
                        color
                        opacity
                        style
                        width
                      }
                      padding {
                        bottom
                        left
                        right
                        top
                      }
                    }
                    headerStyle {
                      background {
                        color
                        opacity
                      }
                      border {
                        color
                        opacity
                        style
                        width
                      }
                      padding {
                        bottom
                        left
                        right
                        top
                      }
                      subTitle {
                        align
                        color
                        family
                        size
                        weight
                      }
                      title {
                        align
                        color
                        family
                        size
                        weight
                      }
                    }
                    headingContentStyle {
                      h1 {
                        align
                        color
                        family
                        size
                        weight
                      }
                      h2 {
                        align
                        color
                        family
                        size
                        weight
                      }
                      h3 {
                        align
                        color
                        family
                        size
                        weight
                      }
                      h4 {
                        align
                        color
                        family
                        size
                        weight
                      }
                    }
                    imageContentStyle {
                      caption {
                        align
                        color
                        family
                        size
                        weight
                      }
                      fit
                    }
                    pageStyle {
                      background {
                        color
                        opacity
                      }
                      margin {
                        bottom
                        left
                        right
                        top
                      }
                    }
                    textContentStyle {
                      content {
                        align
                        color
                        family
                        size
                        weight
                      }
                    }
                    urlContentStyle {
                      url
                    }
                  }
                  containers {
                    id
                    row
                    column
                    width
                    height
                    contentConfiguration {
                      heading {
                        content
                        contentStyle {
                          content {
                            align
                            color
                            family
                            size
                            weight
                          }
                        }
                        variant
                      }
                      image {
                        altText
                        caption
                      }
                      text {
                        content
                        contentStyle {
                          content {
                            align
                            color
                            family
                            size
                            weight
                          }
                        }
                      }
                      url {
                        url
                      }
                    }
                    contentData {
                      data
                      id
                      upload {
                        id
                      }
                    }
                    contentStyle {
                      heading {
                        background {
                          color
                          opacity
                        }
                        border {
                          color
                          opacity
                          style
                          width
                        }
                        padding {
                          bottom
                          left
                          right
                          top
                        }
                        subTitle {
                          align
                          color
                          family
                          size
                          weight
                        }
                        title {
                          align
                          color
                          family
                          size
                          weight
                        }
                      }
                    }
                  }
                }
              }
            }
        '''


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
