import csv
from io import StringIO

from django.db import models

from utils.files import generate_file_for_upload
from deep.filter_set import get_dummy_request
from project.models import ProjectOrganization, ProjectRole, ProjectMembership
from organization.models import Organization
from deep_explore.filter_set import ExploreProjectFilterSet
from deep_explore.schema import get_global_filters, project_queryset


def get_organizations_display(project, organization_type=None):
    organization_ids_qs = ProjectOrganization.objects.filter(project=project)
    if organization_type:
        organization_ids_qs = organization_ids_qs.filter(organization_type=organization_type)
    return ','.join([
        org.data.title
        for org in Organization.objects.filter(
            id__in=organization_ids_qs.values_list('organization', flat=True)
        )
    ])


def generate_projects_stats(filters, user):
    PROJECT_OWNER_ROLE = ProjectRole.objects.get(type=ProjectRole.Type.PROJECT_OWNER)
    filterset_attrs = dict(
        request=get_dummy_request(
            active_project=None,
            user=user,
        ),
    )

    if not filters:
        raise Exception('This should be defined.')

    project_filters = filters.get('project') or {}

    file = StringIO()
    headers = [
        'ID',
        'Title',
        'Created Date',
        'Owners',
        'Start Date',
        'End Date',
        'Last Entry (Date)',
        'Organisation (Project owner)',
        'Project Stakeholders',
        'Geo Areas',
        'Analysis Framework',
        'Description',
        'Status',
        'Test project (Y/N)',
        'Members Count',
        'Sources Count',
        'Entries Count',
        '# of Exports',
    ]

    projects_qs = project_queryset().annotate(
        analysis_framework_title=models.F('analysis_framework__title'),
    )

    projects_qs = ExploreProjectFilterSet(project_filters, queryset=projects_qs, **filterset_attrs).qs
    projects_qs = projects_qs.filter(**get_global_filters(filters))

    writer = csv.DictWriter(file, fieldnames=headers, extrasaction='ignore')
    writer.writeheader()

    for project in projects_qs.order_by('-id'):
        last_entry = project.entry_set.order_by('-id').first()
        owners = ','.join([
            f'{member.member.get_display_name()}'
            for member in ProjectMembership.objects.filter(project=project, role=PROJECT_OWNER_ROLE)
        ])

        regions_qs = project.regions
        members_qs = project.members
        exports_qs = project.export_set
        leads_qs = project.lead_set.filter(**get_global_filters(filters))
        entries_qs = project.entry_set.filter(**get_global_filters(filters))

        writer.writerow({
            'ID': project.id,
            'Title': project.title,
            'Created Date': project.created_at,
            'Owners': owners,
            'Start Date': project.start_date,
            'End Date': project.end_date,
            'Last Entry (Date)': last_entry and last_entry.created_at,
            'Organisation (Project owner)': get_organizations_display(
                project,
                ProjectOrganization.Type.LEAD_ORGANIZATION,
            ),
            'Project Stakeholders': get_organizations_display(project),
            'Geo Areas': ','.join(regions_qs.values_list('title', flat=True).distinct()),
            'Analysis Framework': project.analysis_framework_title,
            'Description': project.description,
            'Status': project.status,
            'Test project (Y/N)': 'Y' if project.is_test else 'N',
            'Members Count': members_qs.count(),
            'Sources Count': leads_qs.count(),
            'Entries Count': entries_qs.count(),
            '# of Exports': exports_qs.count(),
        })
    return generate_file_for_upload(file)


def export_projects_stats(export):
    return generate_projects_stats(
        (export.filters or {}).get('deep_explore') or {},
        export.exported_by,
    )
