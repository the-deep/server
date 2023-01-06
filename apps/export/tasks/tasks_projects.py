import csv
from io import StringIO

from django.db import models

from deep.filter_set import get_dummy_request
from project.models import Project, ProjectOrganization, ProjectRole, ProjectMembership
from organization.models import Organization
from project.filter_set import ProjectGqlFilterSet
from lead.filter_set import LeadGQFilterSet
from entry.filter_set import EntryGQFilterSet


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


def export_projects_stats(export):
    PROJECT_OWNER_ROLE = ProjectRole.objects.get(type=ProjectRole.Type.PROJECT_OWNER)
    filterset_attrs = dict(
        request=get_dummy_request(
            active_project=None,
            user=export.exported_by,
        ),
    )

    filters = export.filters or {}
    projects_filters = filters.get('project') or {}
    leads_filters = filters.get('lead') or {}
    entries_filters = filters.get('entry') or {}

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

    projects_qs = Project.objects.filter(
        is_private=False,
        is_test=False,
    ).annotate(
        analysis_framework_title=models.F('analysis_framework__title'),
    )

    projects_qs = ProjectGqlFilterSet(projects_filters, queryset=projects_qs, **filterset_attrs).qs

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
        leads_qs = LeadGQFilterSet(leads_filters, queryset=project.lead_set, **filterset_attrs).qs
        entries_qs = EntryGQFilterSet(entries_filters, queryset=project.entry_set, **filterset_attrs).qs

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
    return file