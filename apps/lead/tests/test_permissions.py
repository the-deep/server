from deep.tests import TestCase

from lead.models import Lead
from organization.models import Organization
from project.permissions import PROJECT_PERMISSIONS, get_project_permissions_value
from project.models import Project, ProjectRole


class TestLeadPermissions(TestCase):
    def setUp(self):
        super().setUp()
        self.no_lead_creation_role = ProjectRole.objects.create(
            title='No Lead Creation Role',
            lead_permissions=0,
            entry_permissions=get_project_permissions_value('entry', '__all__'),
            setup_permissions=get_project_permissions_value('setup', '__all__'),
            export_permissions=get_project_permissions_value('export', '__all__'),
            assessment_permissions=get_project_permissions_value('assessment', '__all__'),
        )
        self.lead_creation_role = ProjectRole.objects.create(
            title='Lead Creation Role',
            lead_permissions=get_project_permissions_value('lead', ['create']),
            entry_permissions=get_project_permissions_value('entry', '__all__'),
            setup_permissions=get_project_permissions_value('setup', '__all__'),
            export_permissions=get_project_permissions_value('export', '__all__'),
            assessment_permissions=get_project_permissions_value('assessment', '__all__'),
        )
        self.author = self.source = self.create_organization()

    def create_organization(self, **kwargs):
        return self.create(Organization, **kwargs)

    def test_lead_copy_no_permission(self):
        lead_not_modify_permission = 15 ^ (1 << 2)  # Unsetting modify bit (1 << 2)
        lead_not_create_permission = 15 ^ (1 << 1)  # Unsetting create bit (1 << 1)
        project_role = self.create(
            ProjectRole,
            lead_permissions=lead_not_modify_permission & lead_not_create_permission
        )
        source_project = self.create(Project, role=project_role)
        dest_project = self.create(Project)

        lead = self.create(Lead, project=source_project)

        # source_project.add_member(self.user, project_role)

        lead = self.create(Lead, project=source_project)

        data = {
            'projects': [dest_project.pk],
            'leads': [lead.pk],
        }
        url = '/api/v1/lead-copy/'

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_403(response)

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
