from deep.tests import TestCase

from project.models import Project
from user.models import User
from lead.models import Lead
from ary.models import (
    Assessment,
    AssessmentTemplate,
    MetadataGroup, MetadataField, MetadataOption,
    MethodologyGroup,
    Sector,
    AffectedGroup,
)


class AssessmentTests(TestCase):
    def create_lead(self):
        project = self.create(Project, role=self.admin_role)
        return self.create(Lead, project=project)

    def test_create_assessment(self):
        assessment_count = Assessment.objects.count()

        lead = self.create_lead()
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

        self.assertEqual(Assessment.objects.count(), assessment_count + 1)
        self.assertEqual(response.data['version_id'], 1)
        self.assertEqual(response.data['metadata'], data['metadata'])
        self.assertEqual(response.data['methodology'],
                         data['methodology'])

    def test_create_assessment_no_project_yes_lead(self):
        assessment_count = Assessment.objects.count()

        lead = self.create_lead()
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

        self.assertEqual(Assessment.objects.count(), assessment_count + 1)
        self.assertEqual(response.data['version_id'], 1)
        self.assertEqual(response.data['metadata'], data['metadata'])
        self.assertEqual(response.data['methodology'],
                         data['methodology'])

    def test_create_assessment_no_perm(self):
        assessment_count = Assessment.objects.count()

        lead = self.create_lead()
        user = self.create(User)

        lead.project.add_member(user, self.view_only_role)

        url = '/api/v1/assessments/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'metadata': {'test_meta': 'Test'},
            'methodology': {'test_methodology': 'Test'},
        }

        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_403(response)

        self.assertEqual(Assessment.objects.count(), assessment_count)

    def test_lead_assessment(self):
        # First test creating a new assessment for a new lead
        assessment_count = Assessment.objects.count()

        lead = self.create_lead()
        url = '/api/v1/lead-assessments/{}/'.format(lead.pk)
        data = {
            'metadata': {'test_meta': 'Test 1'},
            'methodology': {'test_methodology': 'Test 2'},
        }

        self.authenticate()
        response = self.client.put(url, data)
        self.assert_200(response)

        self.assertEqual(Assessment.objects.count(), assessment_count + 1)
        self.assertEqual(response.data['version_id'], 1)
        self.assertEqual(response.data['metadata'], data['metadata'])
        self.assertEqual(response.data['methodology'],
                         data['methodology'])

        # Next test editing the assessment

        data['metadata'] = {'test_meta': 'Test 1 new'}

        response = self.client.put(url, data)
        self.assert_200(response)

        self.assertEqual(response.data['version_id'], 2)
        self.assertEqual(response.data['metadata'], data['metadata'])

    def test_get_template(self):
        template = self.create(AssessmentTemplate)

        md_group = self.create(MetadataGroup, template=template)
        md_field = self.create(MetadataField, group=md_group)
        self.create(MetadataOption, field=md_field)
        self.create(MetadataOption, field=md_field)
        self.create(MetadataOption, field=md_field)
        self.create(MethodologyGroup, template=template)
        self.create(Sector, template=template)
        self.create(Sector, template=template)
        self.create(Sector, template=template)
        ag_parent = self.create(AffectedGroup, template=template)
        self.create(AffectedGroup, parent=ag_parent, template=template)
        self.create(AffectedGroup, parent=ag_parent, template=template)

        url = '/api/v1/assessment-templates/{}/'.format(template.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        # TODO: More detailed test?

    def test_project_assessment_template(self):
        project = self.create(Project)
        template = self.create(AssessmentTemplate)
        project.assessment_template = template
        project.save()

        url = '/api/v1/projects/{}/assessment-template/'.format(
            project.id
        )

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['id'], template.id)
        self.assertEqual(response.data['title'], template.title)

    def test_options(self):
        url = '/api/v1/assessment-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_ary_copy_from_project_with_only_view(self):
        url = '/api/v1/assessment-copy/'

        source_project = self.create(Project, role=self.view_only_role)
        dest_project = self.create(Project, role=self.admin_role)
        ary = self.create(Assessment, project=source_project, lead=self.create(Lead, project=source_project))

        arys_count = Assessment.objects.all().count()

        data = {
            'projects': [dest_project.pk],
            'assessments': [ary.pk],
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_403(response)

        assert arys_count == Assessment.objects.all().count(), "No new assessment should have been created"

    def test_ary_copy(self):
        url = '/api/v1/assessment-copy/'

        # Projects [Source]
        # NOTE: make sure the source projects have create/edit permissions
        project1s = self.create(Project, title='project1s', role=self.admin_role)
        project2s = self.create(Project, title='project2s', role=self.admin_role)
        project3s = self.create(Project, title='project3s')
        project4s = self.create(Project, title='project4s', role=self.normal_role)

        # Projects [Destination]
        project1d = self.create(Project, title='project1d')
        project2d = self.create(Project, title='project2d', role=self.admin_role)
        project3d = self.create(Project, title='project3d', role=self.ary_create_role)
        project4d = self.create(Project, title='project4d', role=self.view_only_role)

        lead1s = self.create(
            Lead, title='lead1s', source_type=Lead.SourceType.WEBSITE, url='https://random-source-11010', project=project1s)
        lead2s = self.create(
            Lead, title='lead2s', source_type=Lead.SourceType.WEBSITE, url='https://random-source-11011', project=project2s)
        lead3s = self.create(Lead, title='lead3s', project=project3s)
        lead4s = self.create(Lead, title='lead4s', project=project4s)

        # ary1 Info (Will be used later for testing)

        # Generate Assessments
        ary1 = self.create(Assessment, project=lead1s.project, lead=lead1s)
        ary2 = self.create(Assessment, project=lead2s.project, lead=lead2s)
        ary3 = self.create(Assessment, project=lead3s.project, lead=lead3s)
        ary4 = self.create(Assessment, project=lead4s.project, lead=lead4s)

        # For duplicate url validation check
        # Lead + Assessment
        lead1d = self.create(Lead, title='lead1d', source_type=lead1s.source_type, url=lead1s.url, project=project1d)
        self.create(Assessment, project=lead1d.project, lead=lead1d)
        # Only Lead (For project3d so that only 1 Ary is created (with lead view only access) since one lead already exists)
        self.create(Lead, title='lead2d', source_type=lead2s.source_type, url=lead2s.url, project=project3d)

        # Request body data [also contains unauthorized projects and Assessments]
        data = {
            'projects': sorted([project4d.pk, project3d.pk, project2d.pk, project1d.pk, project1s.pk]),
            'assessments': sorted([ary3.pk, ary2.pk, ary1.pk, ary4.pk]),
        }
        # data [only contains authorized projects and assessments]
        validate_data = {
            'projects': sorted([project3d.pk, project2d.pk, project1s.pk]),
            'assessments': sorted([ary4.pk, ary2.pk, ary1.pk]),
        }

        ary_stats = [
            # Project, Original Assessment Count, Assessment Count After Assessment-copy
            (project1s, 1, 3),
            (project2s, 1, 1),
            (project3s, 1, 1),
            (project4s, 1, 1),

            (project1d, 1, 1),
            (project2d, 0, 3),
            (project3d, 0, 1),
            (project4d, 0, 0),
        ]

        # Current ARY Count
        for project, old_ary_count, _ in ary_stats:
            current_ary_count = Assessment.objects.filter(project_id=project.pk).count()
            assert old_ary_count == current_ary_count, f'Project: {project.title} Assessment current count is different'

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        rdata = response.json()
        # Sort the data since we are comparing lists
        sorted_rdata = {
            'projects': sorted(rdata['projects']),
            'assessments': sorted(rdata['assessments']),
        }
        self.assert_201(response)
        self.assertNotEqual(sorted_rdata, data)
        self.assertEqual(sorted_rdata, validate_data)

        # New ARY Count (after assessment-copy)
        for project, _, new_ary_count in ary_stats:
            current_ary_count = Assessment.objects.filter(project_id=project.pk).count()
            # assert new_ary_count == current_ary_count, f'Project: {project.title} Assessment new count is different'
            assert new_ary_count == current_ary_count, f'Project: {project.title} {project.pk} Assessment new count is different'
