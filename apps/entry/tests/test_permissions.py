from deep.tests import TestCase
from entry.models import Lead
from entry.models import Entry
from project.models import Project, ProjectRole
from project.permissions import PROJECT_PERMISSIONS, get_project_permissions_value
from analysis_framework.models import AnalysisFramework


class TestEntryPermissions(TestCase):
    def setUp(self):
        super().setUp()
        self.no_entry_creation_role = ProjectRole.objects.create(
            title='No Lead Creation Role',
            entry_permissions=0,
            lead_permissions=get_project_permissions_value('lead', '__all__'),
            setup_permissions=get_project_permissions_value('setup', '__all__'),
            export_permissions=get_project_permissions_value('export', '__all__'),
            assessment_permissions=get_project_permissions_value('assessment', '__all__'),
        )
        self.entry_creation_role = ProjectRole.objects.create(
            title='Lead Creation Role',
            entry_permissions=get_project_permissions_value('entry', ['create']),
            lead_permissions=get_project_permissions_value('lead', '__all__'),
            setup_permissions=get_project_permissions_value('setup', '__all__'),
            export_permissions=get_project_permissions_value('export', '__all__'),
            assessment_permissions=get_project_permissions_value('assessment', '__all__'),
        )

    def test_cannot_view_confidential_entry_without_permissions(self):
        view_unprotected_role = ProjectRole.objects.create(
            lead_permissions=15,
            entry_permissions=PROJECT_PERMISSIONS.entry.view_only_unprotected,
        )
        project = self.create(Project, role=view_unprotected_role)

        lead1 = self.create(Lead, project=project, confidentiality=Lead.UNPROTECTED)
        lead_confidential = self.create(Lead, project=project, confidentiality=Lead.CONFIDENTIAL)

        entry1 = self.create(Entry, lead=lead1, project=project)
        entry_confidential = self.create(Entry, lead=lead_confidential, project=project)

        url = '/api/v1/entries/'
        self.authenticate()

        resp = self.client.get(url)
        self.assert_200(resp)

        entries_ids = set([x['id'] for x in resp.data['results']])
        assert entries_ids == {entry1.id}

        # Check particular non-confidential entry, should return 200
        url = f'/api/v1/entries/{entry1.id}/'
        self.authenticate()

        resp = self.client.get(url)
        self.assert_200(resp)

        # Check particular confidential entry, should return 404
        url = f'/api/v1/entries/{entry_confidential.id}/'
        self.authenticate()

        resp = self.client.get(url)
        self.assert_404(resp)

    def test_create_entry_no_permission(self):
        # Create project where self.user has no entry creation permission
        af = self.create(AnalysisFramework)
        project = self.create(
            Project,
            analysis_framework=af,
            role=self.no_entry_creation_role
        )
        lead = self.create(Lead, project=project)
        url = '/api/v1/entries/'
        data = {
            'project': project.pk,
            'lead': lead.pk,
            'analysis_framework': project.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': {},
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_403(response)

    def test_create_entry_with_permission(self):
        # Create project where self.user has no entry creation permission
        af = self.create(AnalysisFramework)
        project = self.create(
            Project,
            analysis_framework=af,
            role=self.entry_creation_role
        )
        lead = self.create(Lead, project=project)
        url = '/api/v1/entries/'
        data = {
            'project': project.pk,
            'lead': lead.pk,
            'analysis_framework': project.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': {},
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

    def create_project(self):
        analysis_framework = self.create(AnalysisFramework)
        return self.create(
            Project, analysis_framework=analysis_framework,
            role=self.admin_role
        )

    def create_lead(self, project=None):
        project = project or self.create_project()
        return self.create(Lead, project=project)
