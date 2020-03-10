from deep.tests import TestCase

from lead.models import Lead
from organization.models import Organization
from project.permissions import PROJECT_PERMISSIONS, get_project_permissions_value
from project.models import Project, ProjectRole


class TestLeadPermissions(TestCase):
    def setUp(self):
        super().setUp()
        common_role_attrs = {
            'entry_permissions': get_project_permissions_value('entry', '__all__'),
            'setup_permissions': get_project_permissions_value('setup', '__all__'),
            'export_permissions': get_project_permissions_value('export', '__all__'),
            'assessment_permissions': get_project_permissions_value('assessment', '__all__'),
        }
        self.no_lead_creation_role = ProjectRole.objects.create(
            title='No Lead Creation Role',
            lead_permissions=0,
            **common_role_attrs
        )
        self.lead_creation_role = ProjectRole.objects.create(
            title='Lead Creation Role',
            lead_permissions=get_project_permissions_value('lead', ['create']),
            **common_role_attrs
        )
        self.lead_view_clone_role = ProjectRole.objects.create(
            title='Lead View Role',
            lead_permissions=get_project_permissions_value('lead', ['view', 'create']),
            **common_role_attrs
        )
        self.author = self.source = self.create_organization()

    def create_organization(self, **kwargs):
        return self.create(Organization, **kwargs)

    def test_lead_copy_no_permission(self):
        source_project = self.create(Project, role=self.no_lead_creation_role)
        dest_project = self.create(Project)

        lead = self.create(Lead, project=source_project)

        data = {
            'projects': [dest_project.pk],
            'leads': [lead.pk],
        }
        url = '/api/v1/lead-copy/'

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_403(response)

    def test_lead_copy_with_permission(self):
        # User should have view and create permission in source project in order to clone
        source_project = self.create(Project, role=self.lead_view_clone_role)
        dest_project = self.create(Project, role=self.lead_creation_role)

        lead = self.create(Lead, project=source_project)
        initial_lead_count = Lead.objects.count()

        data = {
            'projects': [dest_project.pk],
            'leads': [lead.pk],
        }
        url = '/api/v1/lead-copy/'

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        assert Lead.objects.count() == initial_lead_count + 1, "One more lead should be created"
        assert Lead.objects.filter(title=lead.title, project=dest_project).exists(),\
            "Exact same lead should be created"

    def test_cannot_view_confidential_lead_without_permissions(self):
        view_unprotected_role = ProjectRole.objects.create(
            lead_permissions=PROJECT_PERMISSIONS.lead.view_only_unprotected,
        )
        project = self.create(Project, role=view_unprotected_role)

        lead1 = self.create_lead(project=project, confidentiality=Lead.UNPROTECTED)
        lead_confidential = self.create_lead(project=project, confidentiality=Lead.CONFIDENTIAL)

        url = '/api/v1/leads/'
        self.authenticate()

        resp = self.client.get(url)
        self.assert_200(resp)

        leads_ids = set([x['id'] for x in resp.data['results']])
        assert leads_ids == {lead1.id}, "Only confidential should be present"

        # Check get particuar non-confidential lead, should return 200
        url = f'/api/v1/leads/{lead1.id}/'
        self.authenticate()

        resp = self.client.get(url)
        self.assert_200(resp)

        # Check get particuar confidential lead, should return 404
        url = f'/api/v1/leads/{lead_confidential.id}/'
        self.authenticate()

        resp = self.client.get(url)
        self.assert_404(resp)

    def test_create_lead_no_permission(self):
        # Create a project where self.user has no lead creation permission
        project = self.create(Project, role=self.no_lead_creation_role)
        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': self.user.id,
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_403(response)

    def test_create_lead_with_permission(self):
        # Create a project where self.user has no lead creation permission
        project = self.create(Project, role=self.lead_creation_role)
        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': self.user.id,
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
