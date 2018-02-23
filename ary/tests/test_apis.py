from rest_framework import status
from rest_framework.test import APITestCase

from user.tests.test_apis import AuthMixin
from lead.tests.test_apis import LeadMixin
from project.tests.test_apis import ProjectMixin
from ary.models import (
    Assessment,
    AssessmentTemplate,
    MetadataGroup, MetadataField, MetadataOption,
    MethodologyGroup,
    AssessmentTopic,
    AffectedGroup,
)


class AssessmentMixin():
    def create_or_get_assessment(self):
        """
        Create new or return recent assessment
        Required mixin: LeadMixin, ProjectMixin
        """
        assessment = Assessment.objects.first()
        if not assessment:
            lead = self.create_or_get_lead()
            assessment = Assessment.objects.create(
                lead=lead,
                meta_data={'test_meta': 'Test'},
                methodology_data={'test_methodology': 'Test'},
            )
        return assessment


class AssessmentTests(AuthMixin, LeadMixin, ProjectMixin,
                      APITestCase):
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION header
        """
        self.auth = self.get_auth()

    def test_create_assessment(self):
        """
        Create Assessment Test
        """
        old_count = Assessment.objects.count()

        url = '/api/v1/assessments/'
        data = {
            'lead': self.create_or_get_lead().pk,
            'meta_data': {'test_meta': 'Test'},
            'methodology_data': {'test_methodology': 'Test'},
        }
        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Assessment.objects.count(), old_count + 1)
        self.assertEqual(response.data['version_id'], 1)
        self.assertEqual(response.data['meta_data'], data['meta_data'])
        self.assertEqual(response.data['methodology_data'],
                         data['methodology_data'])

    def test_get_template(self):
        """
        Test getting assessment template
        Note: there is no API to create template
        """
        template = AssessmentTemplate.objects.create(
            title='Test template',
        )
        md_group = MetadataGroup.objects.create(
            template=template,
            title='Test MD Group',
        )
        MetadataField.objects.create(
            group=md_group,
            title='Test',
            field_type='string',
        )
        md_field = MetadataField.objects.create(
            group=md_group,
            title='Test2',
            field_type='select',
        )
        MetadataOption.objects.create(
            field=md_field,
            title='Test',
        )
        MethodologyGroup.objects.create(
            template=template,
            title='Test MTHD Group',
        )
        AssessmentTopic.objects.create(
            template=template,
            title='Health',
        )
        parent = AffectedGroup.objects.create(
            template=template,
            title='All',
        )
        AffectedGroup.objects.create(
            template=template,
            title='Displaced',
            parent=parent,
        )
        AffectedGroup.objects.create(
            template=template,
            title='Non Displaced',
            parent=parent,
        )

        url = '/api/v1/assessment-templates/{}/'.format(template.id)
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # TODO: More detailed test
