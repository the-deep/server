from deep.tests import TestCase

from lead.models import Lead
from project.models import Project, ProjectRole
from project.permissions import get_project_permissions_value


class TestAssessmentPermissions(TestCase):
    def setUp(self):
        super().setUp()
        self.no_assmt_creation_role = ProjectRole.objects.create(
            title='No Lead Creation Role',
            entry_permissions=get_project_permissions_value('entry', '__all__'),
            lead_permissions=get_project_permissions_value('lead', '__all__'),
            setup_permissions=get_project_permissions_value('setup', '__all__'),
            export_permissions=get_project_permissions_value('export', '__all__'),
            assessment_permissions=0,
        )
        self.assmt_creation_role = ProjectRole.objects.create(
            title='Lead Creation Role',
            entry_permissions=get_project_permissions_value('entry', '__all__'),
            lead_permissions=get_project_permissions_value('lead', '__all__'),
            setup_permissions=get_project_permissions_value('setup', '__all__'),
            export_permissions=get_project_permissions_value('export', '__all__'),
            assessment_permissions=get_project_permissions_value('assessment', ['create']),
        )

    def test_create_assessment_no_permission(self):
        project = self.create(
            Project,
            role=self.no_assmt_creation_role
        )
        lead = self.create(Lead, project=project)

        url = '/api/v1/assessments/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'metadata': {'test_meta': 'Test'},
            'methodology': {'test_methodology': 'Test'},
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_403(response)

    def test_create_assessment_with_permission(self):
        project = self.create(
            Project,
            role=self.assmt_creation_role
        )
        lead = self.create(Lead, project=project)
        url = '/api/v1/assessments/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'metadata': {'test_meta': 'Test'},
            'methodology': {'test_methodology': 'Test'},
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
