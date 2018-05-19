from deep.tests import TestCase

from project.models import Project
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
        project = self.create(Project)
        return self.create(Lead, project=project)

    def test_create_assessment(self):
        assessment_count = Assessment.objects.count()

        url = '/api/v1/assessments/'
        data = {
            'lead': self.create_lead().pk,
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
