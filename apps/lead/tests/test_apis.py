import logging
from datetime import date
import uuid

from django.db.models import Q
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.exceptions import ErrorDetail

from utils.common import UidBase64Helper
from deep.tests import TestCase

from user.models import User
from user.serializers import SimpleUserSerializer
from project.models import (
    Project, ProjectMembership,
    ProjectUserGroupMembership,
)
from project.serializers import SimpleProjectSerializer
from geo.models import Region

from organization.models import (
    Organization,
    OrganizationType,
)
from organization.serializers import SimpleOrganizationSerializer
from lead.filter_set import LeadFilterSet
from lead.serializers import SimpleLeadGroupSerializer
from deepl_integration.handlers import AutoAssistedTaggingDraftEntryHandler, LeadExtractionHandler
from deepl_integration.serializers import DeeplServerBaseCallbackSerializer
from entry.models import (
    Entry,
    ProjectEntryLabel,
    LeadEntryGroup,
    EntryGroupLabel,
)
from lead.models import (
    Lead,
    LeadPreview,
    LeadPreviewAttachment,
    EMMEntity,
    LeadEMMTrigger,
    LeadGroup,
)
from user_group.models import UserGroup, GroupMembership
from ary.models import Assessment
from lead.factories import LeadFactory, LeadPreviewFactory
from unittest import mock


logger = logging.getLogger(__name__)

# Organization data
RELIEFWEB_DATA = {
    'title': 'Reliefweb',
    'short_name': 'reliefweb',
    'long_name': 'reliefweb.int',
    'url': 'https://reliefweb.int',
}
REDHUM_DATA = {
    'title': 'Redhum',
    'short_name': 'redhum',
    'long_name': 'redhum.org',
    'url': 'https://redhum.org',
}
UNHCR_DATA = {
    'title': 'UNHCR',
    'short_name': 'unhcr',
    'long_name': 'United Nations High Commissioner for Refugees',
    'url': 'https://www.unhcr.org',
}


class LeadTests(TestCase):
    def setUp(self):
        super().setUp()
        self.author = self.source = self.create_organization()

    def create_organization(self, **kwargs):
        return self.create(Organization, **kwargs)

    def test_create_lead(self, assignee=None):
        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.Confidentiality.UNPROTECTED,
            'status': Lead.Status.NOT_TAGGED,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': assignee or self.user.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Lead.objects.count(), lead_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['assignee'], self.user.id)

        # low is default priority
        self.assertEqual(r_data['priority'], Lead.Priority.LOW)

    def test_lead_create_with_status_validated(self, assignee=None):
        lead_begining = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.Confidentiality.UNPROTECTED,
            'status': Lead.Status.TAGGED,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': assignee or self.user.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Lead.objects.count(), lead_begining + 1)
        r_data = response.data
        self.assertEqual(r_data['status'], data['status'])

    def test_pre_bulk_delete_leads(self):
        project = self.create(Project)
        lead1 = self.create(Lead, project=project)
        lead3 = self.create(Lead, project=project)

        lead_ids = [lead1.id, lead3.id]
        admin_user = self.create(User)
        project.add_member(admin_user, role=self.admin_role)
        url = '/api/v1/project/{}/leads/dry-bulk-delete/'.format(project.id)
        self.authenticate(admin_user)
        response = self.client.post(url, {'leads': lead_ids})
        self.assert_200(response)
        r_data = response.data
        self.assertIn('entries', r_data)

    def test_bulk_delete_leads(self):
        project = self.create(Project)
        lead1 = self.create(Lead, project=project)
        self.create(Lead, project=project)
        lead3 = self.create(Lead, project=project)
        lead_count = Lead.objects.count()

        lead_ids = [lead1.id, lead3.id]
        url = '/api/v1/project/{}/leads/bulk-delete/'.format(project.id)

        # calling without delete permissions
        view_user = self.create(User)
        project.add_member(view_user, role=self.view_only_role)
        self.authenticate(view_user)
        response = self.client.post(url, {'leads': lead_ids})
        self.assert_403(response)

        admin_user = self.create(User)
        project.add_member(admin_user, role=self.admin_role)
        self.authenticate(admin_user)
        response = self.client.post(url, {'leads': lead_ids})
        self.assert_204(response)

        self.assertLess(Lead.objects.count(), lead_count)

    def test_create_high_priority_lead(self, assignee=None):
        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.Confidentiality.UNPROTECTED,
            'status': Lead.Status.NOT_TAGGED,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': assignee or self.user.id,
            'priority': Lead.Priority.HIGH,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Lead.objects.count(), lead_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['assignee'], self.user.id)

        # low is default priority
        self.assertEqual(r_data['priority'], Lead.Priority.HIGH)

    def test_create_lead_with_emm(self):
        entity1 = self.create(EMMEntity, name='entity1')
        entity2 = self.create(EMMEntity, name='entity2')
        entity3 = self.create(EMMEntity, name='entity3')

        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.Confidentiality.UNPROTECTED,
            'status': Lead.Status.NOT_TAGGED,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': self.user.id,
            'emm_entities': [
                {'name': entity1.name},
                {'name': entity2.name},
            ],
            'emm_triggers': [
                {'emm_keyword': 'kw', 'emm_risk_factor': 'rf', 'count': 3},
                {'emm_keyword': 'kw1', 'emm_risk_factor': 'rf1', 'count': 6},
            ]
        }

        self.authenticate()
        response = self.client.post(url, data, format='json')
        self.assert_201(response)

        self.assertEqual(Lead.objects.count(), lead_count + 1)
        r_data = response.data
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['assignee'], self.user.id)

        assert 'emm_entities' in r_data
        assert 'emm_triggers' in r_data
        assert len(r_data['emm_entities']) == 2
        assert len(r_data['emm_triggers']) == 2

        lead_id = r_data['id']

        # Check emm triggers created
        assert LeadEMMTrigger.objects.filter(lead_id=lead_id).count() == 2

        # This should not change anything in the database
        data['emm_triggers'] = None
        data['emm_entities'] = [{'name': entity3.name}]
        response = self.client.put(f"{url}{r_data['id']}/", data, format='json')
        self.assert_200(response)
        assert 'emm_entities' in r_data
        assert 'emm_triggers' in r_data
        assert len(r_data['emm_entities']) == 2
        assert len(r_data['emm_triggers']) == 2

    def test_get_lead_check_no_of_entries(self, assignee=None):
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.Confidentiality.UNPROTECTED,
            'status': Lead.Status.NOT_TAGGED,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': assignee or self.user.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        url = '/api/v1/leads/'

        response = self.client.get(url)

        r_data = response.json()
        assert 'entriesCount' in r_data['results'][0]

    def test_create_lead_no_create_role(self, assignee=None):
        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        test_user = self.create(User)
        project.add_member(test_user, role=self.view_only_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.Confidentiality.UNPROTECTED,
            'status': Lead.Status.NOT_TAGGED,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': assignee or self.user.id,
        }

        self.authenticate(test_user)
        response = self.client.post(url, data)
        self.assert_403(response)

        self.assertEqual(Lead.objects.count(), lead_count)

    def test_delete_lead(self):
        project = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project)
        url = '/api/v1/leads/{}/'.format(lead.id)

        self.authenticate()
        response = self.client.delete(url)
        self.assert_204(response)

    def test_delete_lead_no_perm(self):
        project = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project)
        user = self.create(User)

        project.add_member(user, self.view_only_role)

        url = '/api/v1/leads/{}/'.format(lead.id)

        self.authenticate(user)
        response = self.client.delete(url)
        self.assert_403(response)

    def test_multiple_assignee(self):
        self.test_create_lead([self.user.id])

    def test_update_assignee(self):
        # Since we have multiple assignee supported in the Lead model
        # but currently we have only restricted assignee to single value
        # in the API, check if it works in the `update` request

        project = self.create(Project, role=self.admin_role)
        user = self.create(User)
        self.create(ProjectMembership, project=project, member=user)
        lead = self.create(Lead, project=project)

        url = '/api/v1/leads/{}/'.format(lead.id)
        data = {
            'assignee': user.id,
        }

        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_200(response)

        r_data = response.json()
        self.assertEqual(r_data['assignee'], user.id)
        lead = Lead.objects.get(id=lead.id)
        self.assertEqual(lead.get_assignee().id, user.id)

    def test_options(self):
        def check_default_options(rdata):
            for option, value in DEFAULT_OPTIONS.items():
                assert rdata[option] == value, f'value should be same for <{option}> DEFAULT_OPTIONS'

        def assert_id(returned_obj, excepted_obj):
            assert set([obj['id'] for obj in returned_obj]) ==\
                set([obj['id'] for obj in excepted_obj])

        url = '/api/v1/lead-options/'

        # Project
        project = self.create(Project)

        # Sample Organizations
        reliefweb = self.create(Organization, **RELIEFWEB_DATA)
        unhcr = self.create(Organization, **UNHCR_DATA)

        # Sample Lead Groups
        lead_group1 = self.create(LeadGroup, project=project)
        lead_group2 = self.create(LeadGroup, project=project)

        # Sample Members
        out_user = self.create_user()
        user = self.create_user()
        user1 = self.create_user()
        user2 = self.create_user()
        project.add_member(user, role=self.normal_role)
        project.add_member(user1, role=self.normal_role)
        project.add_member(user2, role=self.normal_role)

        # Default options
        DEFAULT_OPTIONS = {
            'confidentiality': [
                {'key': c[0], 'value': c[1]} for c in Lead.Confidentiality.choices
            ],
            'status': [
                {'key': s[0], 'value': s[1]} for s in Lead.Status.choices
            ],
            'priority': [
                {'key': s[0], 'value': s[1]} for s in Lead.Priority.choices
            ],
        }

        self.authenticate(user)

        # 404 if user is not member of any one of the projects
        data = {
            'projects': [project.pk + 1],
        }
        response = self.client.post(url, data)
        self.assert_404(response)

        # 200 if user is member of one of the project [Also other data are filtered by those projects]
        data = {
            'projects': [project.pk + 1, project.pk],
            'leadGroups': [lead_group1.pk, lead_group2.pk],
            'members': [user1.pk, user2.pk],
            'organizations': [reliefweb.pk, unhcr.pk]
        }

        response = self.client.post(url, data)
        self.assert_200(response)

        self.maxDiff = None
        # Only members(all) are returned when requested is None
        data = {
            'projects': [project.pk],
        }
        response = self.client.post(url, data)
        rdata = response.data
        assert 'has_emm_leads' in rdata
        assert not rdata['has_emm_leads'], 'There should be no emm leads in the project'
        assert_id(rdata['members'], SimpleUserSerializer([user1, user2, user], many=True).data)
        assert rdata['projects'] == SimpleProjectSerializer([project], many=True).data
        assert rdata['lead_groups'] == []
        assert rdata['organizations'] == []
        check_default_options(rdata)

        # If value are provided respective data are provided (filtered by permission)
        data = {
            'projects': [project.pk],
            'leadGroups': [lead_group2.pk],
            'members': [user1.pk, user2.pk, out_user.pk],
            'organizations': [unhcr.pk]
        }
        response = self.client.post(url, data)
        rdata = response.data
        assert_id(rdata['members'], SimpleUserSerializer([user1, user2], many=True).data)
        assert rdata['projects'] == SimpleProjectSerializer([project], many=True).data
        assert rdata['lead_groups'] == SimpleLeadGroupSerializer([lead_group2], many=True).data
        assert rdata['organizations'] == SimpleOrganizationSerializer([unhcr], many=True).data
        check_default_options(rdata)

        assert 'emm_entities' in rdata
        assert 'emm_keywords' in rdata
        assert 'emm_risk_factors' in rdata

    def test_emm_options_post(self):
        url = '/api/v1/lead-options/'

        project = self.create_project()

        # Create Entities
        entity1 = self.create(EMMEntity, name='entity1')
        entity2 = self.create(EMMEntity, name='entity2')
        entity3 = self.create(EMMEntity, name='enitty3')
        entity4 = self.create(EMMEntity, name='entity4')  # noqa:F841

        lead1 = self.create_lead(project=project, emm_entities=[entity1])
        lead2 = self.create_lead(project=project, emm_entities=[entity2, entity3])
        lead3 = self.create_lead(project=project, emm_entities=[entity2])
        lead4 = self.create_lead(project=project)

        # Create LeadEMMTrigger objects with
        self.create(
            LeadEMMTrigger, lead=lead1, count=5,
            emm_keyword='keyword1', emm_risk_factor='rf1',
        )
        self.create(
            LeadEMMTrigger, lead=lead2, count=3,
            emm_keyword='keyword1', emm_risk_factor='rf2',
        )
        self.create(
            LeadEMMTrigger, lead=lead3, count=3,
            emm_keyword='keyword2', emm_risk_factor='rf2',
        )
        self.create(
            LeadEMMTrigger, lead=lead4, count=3,
            emm_keyword='keyword1', emm_risk_factor='rf1',
        )

        data = {
            'projects': [project.id],
        }
        self.authenticate()
        response = self.client.post(url, data, format='json')
        self.assert_200(response)
        data = response.data

        # No data should be present when not specified in the query
        assert 'emm_entities' in data
        assert data['emm_entities'] == []

        assert 'emm_keywords' in data
        assert data['emm_keywords'] == []

        assert 'emm_risk_factors' in data
        assert data['emm_risk_factors'] == []

        assert 'has_emm_leads' in data
        assert data['has_emm_leads'], 'There are emm leads'

        data = {
            'projects': [project.id],
            'emm_risk_factors': ['rf1'],  # Only risk factors present
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_200(response)
        data = response.data

        # Check emm_entities
        assert 'emm_entities' in data
        assert not data['emm_entities'], 'Entities not specified.'

        # Check emm_risk_factors
        assert 'emm_risk_factors' in data
        expected_risk_factors_count_set = {('rf1', 'rf1', 8)}
        result_risk_factors_count_set = {(x['key'], x['label'], x['total_count']) for x in data['emm_risk_factors']}
        assert expected_risk_factors_count_set == result_risk_factors_count_set

        # Check emm_keywords
        assert 'emm_keywords' in data
        assert not data['emm_entities'], 'Keywords not specified.'

        assert 'has_emm_leads' in data
        assert data['has_emm_leads'], 'There are emm leads'

    def test_options_assignees_get(self):
        url = '/api/v1/lead-options/?projects={}'
        user = self.create(User)
        project = self.create(Project, title='p1')  # self.user is member
        project.add_member(user)  # Add user to project
        project.add_member(self.user)
        project1 = self.create(Project, title='p2')
        project1.add_member(self.user)

        # Add usergroup as well
        usergroup = self.create(UserGroup)
        ugmember = self.create(User)
        GroupMembership.objects.create(group=usergroup, member=ugmember)
        non_member = self.create(User)

        ProjectUserGroupMembership.objects.create(project=project, usergroup=usergroup)

        projects = f'{project.id}'
        self.authenticate()
        resp = self.client.get(url.format(projects))

        self.assert_200(resp)

        data = resp.data
        assignee_ids = [int(x['key']) for x in data['assignee']]

        assert 'assignee' in data
        # BOTH users should be in assignee since only one project is requested
        assert self.user.id in assignee_ids
        assert user.id in assignee_ids
        assert ugmember.id in assignee_ids
        assert non_member.id not in assignee_ids

        projects = f'{project.id},{project1.id}'

        self.authenticate()
        resp = self.client.get(url.format(projects))

        self.assert_200(resp)

        data = resp.data

        assert 'assignee' in data
        assignee_ids = [int(x['key']) for x in data['assignee']]
        assert self.user.id in assignee_ids
        assert user.id not in assignee_ids
        assert non_member.id not in assignee_ids

    def test_emm_options_get(self):
        project = self.create_project()
        project1 = self.create_project()

        # Create Entities
        entity1 = self.create(EMMEntity, name='entity1')
        entity2 = self.create(EMMEntity, name='entity2')
        entity3 = self.create(EMMEntity, name='entity3')
        entity4 = self.create(EMMEntity, name='entity4')  # noqa:F841

        lead1 = self.create_lead(project=project, emm_entities=[entity1])
        lead2 = self.create_lead(project=project, emm_entities=[entity2, entity3])
        lead3 = self.create_lead(project=project, emm_entities=[entity2])
        lead4 = self.create_lead(project=project)

        # Create leads for project1 as well
        self.create_lead(project=project1, emm_entities=[])
        self.create_lead(project=project1, emm_entities=[])

        # Create LeadEMMTrigger objects with
        self.create(
            LeadEMMTrigger, lead=lead1, count=5,
            emm_keyword='keyword1', emm_risk_factor='rf1',
        )
        self.create(
            LeadEMMTrigger, lead=lead2, count=3,
            emm_keyword='keyword1', emm_risk_factor='rf2',
        )
        self.create(
            LeadEMMTrigger, lead=lead3, count=3,
            emm_keyword='keyword2', emm_risk_factor='rf2',
        )
        self.create(
            LeadEMMTrigger, lead=lead4, count=3,
            emm_keyword='keyword1', emm_risk_factor='',  # This should not be present as risk factor
        )
        # NOTE: 3 leads with keyword keyword1, one with keyword2
        # 2 leads with factor rf1, 2 with factor rf2

        url = f'/api/v1/lead-options/?projects={project.id}'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data

        # Check emm_entities
        assert 'emm_entities' in data
        expected_entity_count_set = {
            (entity1.id, entity1.name, 1),
            (entity2.id, entity2.name, 2),
            (entity3.id, entity3.name, 1)}
        result_entity_count_set = {(x['key'], x['label'], x['total_count']) for x in data['emm_entities']}
        assert expected_entity_count_set == result_entity_count_set

        # Check emm_risk_factors
        assert 'emm_risk_factors' in data
        expected_risk_factors_count_set = {('rf1', 'rf1', 5), ('rf2', 'rf2', 6)}
        result_risk_factors_count_set = {(x['key'], x['label'], x['total_count']) for x in data['emm_risk_factors']}
        assert expected_risk_factors_count_set == result_risk_factors_count_set

        # Check emm_keywords
        assert 'emm_keywords' in data
        expected_keywords_count_set = {('keyword1', 'keyword1', 11), ('keyword2', 'keyword2', 3)}
        result_keywords_count_set = {(x['key'], x['label'], x['total_count']) for x in data['emm_keywords']}
        assert expected_keywords_count_set == result_keywords_count_set

        assert 'has_emm_leads' in data
        assert data['has_emm_leads'], 'There are emm leads'

        # Now check options for project1, there should be no emm related data
        url = f'/api/v1/lead-options/?projects={project1.id}'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data

        assert 'has_emm_leads' in data
        assert not data['has_emm_leads'], 'this Project should not have emm'
        assert 'emm_risk_factors' in data
        assert not data['emm_risk_factors']
        assert 'emm_keywords' in data
        assert not data['emm_keywords']
        assert 'emm_entities' in data
        assert not data['emm_entities']

    def test_trigger_api(self):
        project = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project)
        url = '/api/v1/lead-extraction-trigger/{}/'.format(lead.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_multiple_project(self):
        project1 = self.create(Project, role=self.admin_role)
        project2 = self.create(Project, role=self.admin_role)

        lead_count = Lead.objects.count()

        url = '/api/v1/leads/'
        data = {
            'title': 'test title',
            'project': [project1.id, project2.id],
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.Confidentiality.UNPROTECTED,
            'status': Lead.Status.NOT_TAGGED,
            'text': 'this is some random text',
            'assignee': self.user.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        r_data = response.json()
        self.assertEqual(Lead.objects.count(), lead_count + 2)
        self.assertEqual(len(r_data), 2)

        self.assertEqual(r_data[0].get('project'), project1.id)
        self.assertEqual(r_data[1].get('project'), project2.id)

    def test_url_exists(self):
        project = self.create(Project, role=self.admin_role)
        common_url = 'https://same.com/'
        lead1 = self.create(Lead, source_type='website',
                            project=project,
                            url=common_url)
        lead2 = self.create(Lead, source_type='website',
                            project=project,
                            url='https://different.com/')

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'source_type': 'website',
            'url': common_url,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)

        url = '/api/v1/leads/{}/'.format(lead2.id)
        data = {
            'url': common_url,
        }

        response = self.client.patch(url, data)
        self.assert_400(response)

        # This should not be raised while editing same lead

        url = '/api/v1/leads/{}/'.format(lead1.id)
        data = {
            'title': 'Spaceship allegedly spotted in sky'
        }
        response = self.client.patch(url, data)
        self.assert_200(response)

    def test_lead_copy_from_project_with_only_view(self):
        url = '/api/v1/lead-copy/'

        source_project = self.create(Project, role=self.view_only_role)
        dest_project = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=source_project)

        leads_count = Lead.objects.all().count()

        data = {
            'projects': [dest_project.pk],
            'leads': [lead.pk],
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_403(response)

        assert leads_count == Lead.objects.all().count(), 'No new lead should have been created'

    def test_lead_copy(self):
        url = '/api/v1/lead-copy/'

        # Projects [Source]
        # NOTE: make sure the source projects have create/edit permissions
        project1s = self.create(Project, title='project1s', role=self.admin_role)
        project2s = self.create(Project, title='project2s', role=self.admin_role)
        project3s = self.create(Project, title='project3s')
        project4s = self.create(Project, title='project4s', role=self.normal_role)

        # Projects [Destination]
        project1d = self.create(Project, title='project1d')
        project2d = self.create(Project, title='project2d', role=self.admin_role)
        project3d = self.create(Project, title='project3d', role=self.admin_role)
        project4d = self.create(Project, title='project4d', role=self.view_only_role)

        # Lead1 Info (Will be used later for testing)
        lead1_title = 'Lead 1 2019--222-'
        lead1_text_extract = 'This is a test text extract'
        lead1_preview_file = 'invalid_test_file'
        author = self.create(Organization, title='blablaone')
        author2 = self.create(Organization, title='blablatwo')
        emm_keyword = 'emm1'
        emm_risk_factor = 'risk1'
        emm_count = 22
        emm_entity_name = 'emm_entity_11'

        # Generate Leads
        lead1 = self.create(
            Lead, title=lead1_title, project=project1s, source_type=Lead.SourceType.WEBSITE, url='http://example.com'
        )
        lead1.authors.set([author, author2])
        lead2 = self.create(Lead, project=project2s)
        lead3 = self.create(Lead, project=project3s)
        lead4 = self.create(Lead, project=project4s)

        # For duplicate url validation check
        self.create(
            Lead, title=lead1_title, project=project2d, source_type=Lead.SourceType.WEBSITE, url='http://example.com'
        )

        # Generating Foreign elements for lead1
        self.create(LeadPreview, lead=lead1, text_extract=lead1_text_extract)
        self.create(LeadPreviewAttachment, lead=lead1, file=lead1_preview_file)
        emm_trigger = self.create(
            LeadEMMTrigger, lead=lead1, emm_keyword=emm_keyword, emm_risk_factor=emm_risk_factor, count=emm_count)
        lead1.emm_entities.set([self.create(EMMEntity, name=emm_entity_name)])

        # Request body data [also contains unauthorized projects and leads]
        data = {
            'projects': sorted([project4d.pk, project3d.pk, project2d.pk, project1d.pk, project1s.pk]),
            'leads': sorted([lead3.pk, lead2.pk, lead1.pk, lead4.pk]),
        }
        # data [only contains authorized projects and leads]
        validate_data = {
            'projects': sorted([project3d.pk, project2d.pk, project1s.pk]),
            'leads': sorted([lead4.pk, lead2.pk, lead1.pk]),
        }

        lead_stats = [
            # Project, Original Lead Count, Lead Count After lead-copy
            (project1s, 1, 3),
            (project2s, 1, 1),
            (project3s, 1, 1),
            (project4s, 1, 1),

            (project1d, 0, 0),
            (project2d, 0, 3),
            (project3d, 0, 3),
            (project4d, 0, 0),
        ]

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        rdata = response.json()
        # Sort the data since we are comparing lists
        sorted_rdata = {
            'projects': sorted(rdata['projects']),
            'leads': sorted(rdata['leads']),
        }
        self.assert_201(response)
        self.assertNotEqual(sorted_rdata, data)
        self.assertEqual(sorted_rdata, validate_data)

        for project, old_lead_count, new_lead_count in lead_stats:
            current_lead_count = Lead.objects.filter(project_id=project.pk).count()
            assert new_lead_count == current_lead_count, f'Project: {project.title} lead count is different'

        # Test Foreign Fields
        self.assertEqual(
            Lead.objects.filter(title=lead1_title).count(),
            3,
            'Should have been 3: Original + Custom created + Copy(of original)'
        )
        self.assertEqual(
            Lead.objects.filter(title=lead1_title).exclude(
                Q(pk=lead1.pk) | Q(project=project2d)
            ).count(),
            1,
            'Should have been 1: Copy(of original)'
        )
        lead1_copy = Lead.objects.filter(title=lead1_title).exclude(
            Q(pk=lead1.pk) | Q(project=project2d)
        ).get()
        lead1_copy.refresh_from_db()
        self.assertEqual(
            lead1_copy.images.count(),
            lead1.images.count(),
        )
        self.assertEqual(
            lead1_copy.emm_triggers.count(),
            lead1.emm_triggers.count(),
        )
        emm_trigger = lead1_copy.emm_triggers.filter(emm_risk_factor=emm_risk_factor, emm_keyword=emm_keyword)[0]
        assert lead1_copy.authors.count() == 2
        assert sorted(lead1_copy.authors.values_list('id', flat=True)) == [author.id, author2.id]
        assert lead1_copy.leadpreview.text_extract == lead1_text_extract
        assert lead1_copy.images.all()[0].file == lead1_preview_file
        assert emm_trigger.count == emm_count
        assert lead1_copy.emm_entities.all()[0].name == emm_entity_name

    def test_lead_duplicate_validation(self):
        url = '/api/v1/leads/'
        project = self.create_project()
        file = self.create_gallery_file()

        # Test using FILE (HASH)
        data = {
            'title': 'test title',
            'project': project.pk,
            'source': self.source.pk,
            'author': self.author.pk,
            'source_type': Lead.SourceType.DISK,
            'confidentiality': Lead.Confidentiality.UNPROTECTED,
            'status': Lead.Status.NOT_TAGGED,
            'attachment': {'id': file.pk},
            'assignee': self.user.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        response = self.client.post(url, data)
        self.assert_400(response)

        # Test using TEXT
        data = {
            'title': 'test title',
            'project': project.pk,
            'source': self.source.pk,
            'author': self.author.pk,
            'source_type': Lead.SourceType.TEXT,
            'confidentiality': Lead.Confidentiality.UNPROTECTED,
            'status': Lead.Status.NOT_TAGGED,
            'text': 'duplication test 101',
            'assignee': self.user.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        response = self.client.post(url, data)
        self.assert_400(response)

    def test_lead_order_by_priority(self):
        project = self.create(Project)
        project.add_member(self.user)

        self.create_lead(project=project, priority=Lead.Priority.HIGH)
        self.create_lead(project=project, priority=Lead.Priority.MEDIUM)
        self.create_lead(project=project, priority=Lead.Priority.HIGH)
        self.create_lead(project=project, priority=Lead.Priority.LOW)

        url = '/api/v1/leads/?ordering=priority'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        leads = response.data['results']
        assert leads[0]['priority'] == Lead.Priority.LOW
        assert leads[1]['priority'] == Lead.Priority.MEDIUM
        assert leads[2]['priority'] == Lead.Priority.HIGH
        assert leads[3]['priority'] == Lead.Priority.HIGH

        url = '/api/v1/leads/?ordering=-priority'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        leads = response.data['results']
        assert leads[0]['priority'] == Lead.Priority.HIGH
        assert leads[1]['priority'] == Lead.Priority.HIGH
        assert leads[2]['priority'] == Lead.Priority.MEDIUM
        assert leads[3]['priority'] == Lead.Priority.LOW

    def test_lead_order_by_page_count(self):
        # Create lead and lead_previews
        project = self.create(Project)
        project.add_member(self.user)

        lead1 = self.create(Lead, project=project)
        self.create(LeadPreview, lead=lead1, page_count=20)

        lead2 = self.create(Lead, project=project)
        self.create(LeadPreview, lead=lead2, page_count=15)

        lead3 = self.create(Lead, project=project)
        self.create(LeadPreview, lead=lead3, page_count=None)

        # Ascending ordering
        url = '/api/v1/leads/?ordering=,page_count,,'  # this also tests leading/trailing/multiple commas
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        assert len(response.data['results']) == 3, 'Three leads created'
        leads = response.data['results']
        assert leads[0]['id'] == lead3.id, 'Preview3 has no pages'
        assert leads[1]['id'] == lead2.id, 'Preview2 has less pages'
        assert leads[2]['id'] == lead1.id, 'Preview1 has more pages'

        # Descending ordering
        url = '/api/v1/leads/?ordering=,-page_count,,'  # this also tests leading/trailing/multiple commas
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        assert len(response.data['results']) == 3, 'Three leads created'
        leads = response.data['results']
        assert leads[0]['id'] == lead1.id, 'Preview1 has more pages'
        assert leads[1]['id'] == lead2.id, 'Preview2 has less pages'
        assert leads[2]['id'] == lead3.id, 'Preview3 has no pages'

    def test_lead_filter(self):
        project = self.create_project(create_assessment_template=True)
        project2 = self.create_project(create_assessment_template=True)

        lead1 = self.create_lead(project=project)
        lead2 = self.create_lead(project=project)
        lead3 = self.create_lead(project=project)
        lead4 = self.create_lead(project=project2, priority=Lead.Priority.HIGH)

        self.authenticate()

        response = self.client.get(f'/api/v1/leads/?project={project2.pk}&priority={Lead.Priority.HIGH}')
        assert response.json()['results'][0]['id'] == lead4.pk

        url = f'/api/v1/leads/?project={project.pk}'

        # Project filter test
        response = self.client.get(url)
        assert response.json()['count'] == 3, 'Lead count should be 3'

        # Entries exists filter test
        self.create_entry(lead=lead1)
        self.create_entry(lead=lead2)
        response = self.client.get(f'{url}&exists={LeadFilterSet.Exists.ENTRIES_EXISTS}')
        assert response.json()['count'] == 2, 'Lead count should be 2 for lead with entries'

        # Entries do not exist filter test
        response = self.client.get(f'{url}&exists={LeadFilterSet.Exists.ENTRIES_DO_NOT_EXIST}')
        assert response.json()['count'] == 1, 'Lead count should be 1 for lead without entries'

        # Assessment exists filter test
        self.create_assessment(lead=lead1)
        self.create_assessment(lead=lead3)
        response = self.client.get(f'{url}&exists={LeadFilterSet.Exists.ASSESSMENT_EXISTS}')
        assert response.json()['count'] == 2, 'Lead count should be 2 for lead with assessment'

        # Assessment does not exist filter test
        response = self.client.get(f'{url}&exists={LeadFilterSet.Exists.ASSESSMENT_DOES_NOT_EXIST}')
        assert response.json()['count'] == 1, 'Lead count should be 1 for lead without assessment'

    def test_lead_assignee_filter(self):
        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        project = self.create_project()
        self.create_lead(project=project, assignee=[user1, user2])
        self.create_lead(project=project, assignee=[user1])
        self.create_lead(project=project, assignee=[user2])
        url = f'/api/v1/leads/?assignee={user1.id}'

        # authenticate user
        self.authenticate()

        # filter by user who is assignee in some leads
        response = self.client.get(url)
        assert len(response.data['results']) == 2

        # filter by user who is not assignee in any of the lead
        url = f'/api/v1/leads/?assignee={user3.id}'
        response = self.client.get(url)
        assert len(response.data['results']) == 0

    def test_lead_authoring_organization_type_filter(self):
        url = '/api/v1/leads/?authoring_organization_types={}'

        project = self.create_project(title='lead_test_project')
        organization_type1 = self.create(OrganizationType, title='National')
        organization_type2 = self.create(OrganizationType, title='International')
        organization_type3 = self.create(OrganizationType, title='Government')

        organization1 = self.create(Organization, organization_type=organization_type1)
        organization2 = self.create(Organization, organization_type=organization_type2)
        organization3 = self.create(Organization, organization_type=organization_type3)
        organization4 = self.create(Organization, parent=organization1)

        # create lead
        self.create(Lead, project=project, authors=[organization1])
        self.create(Lead, project=project, authors=[organization2])
        self.create(Lead, project=project, authors=[organization3, organization2])
        self.create(Lead, project=project, authors=[organization4])
        self.authenticate()

        # Authoring organization_type filter test
        response = self.client.get(url.format(organization_type1.id))
        self.assert_200(response)
        assert len(response.data['results']) == 2, 'There should be 2 lead'

        # get multiple leads
        organization_type_query = ','.join([
            str(id) for id in [organization_type1.id, organization_type3.id]
        ])
        response = self.client.get(url.format(organization_type_query))
        assert len(response.data['results']) == 3, 'There should be 3 lead'

        # test authoring_organization post filter
        url = '/api/v1/leads/filter/'
        filter_data = {'authoring_organization_types': [organization_type1.id]}
        self.authenticate()
        response = self.client.post(url, data=filter_data, format='json')
        assert len(response.data['results']) == 2, 'There should be 2 lead'

        # test multiple post
        filter_data = {'authoring_organization_types': [organization_type1.id, organization_type3.id]}
        self.authenticate()
        response = self.client.post(url, filter_data, format='json')
        assert len(response.data['results']) == 3, 'There should be 3 lead'

    def test_lead_filter_search(self):
        url = '/api/v1/leads/?emm_entities={}'
        project = self.create_project()
        lead1 = self.create(Lead, project=project, title='mytext')
        lead2 = self.create(Lead, project=project, source_raw='thisis_mytext')
        self.create(Lead, project=project)
        self.create(Lead, project=project, title='nothing_here')

        url = '/api/v1/leads/?search={}'
        self.authenticate()
        resp = self.client.get(url.format('mytext'))
        self.assert_200(resp)

        expected_ids = {lead1.id, lead2.id}
        obtained_ids = {x['id'] for x in resp.data['results']}
        assert expected_ids == obtained_ids

        url = '/api/v1/leads/filter/'
        post_data = {'search': 'mytext'}
        self.authenticate()
        resp = self.client.post(url, post_data)
        self.assert_200(resp)
        obtained_ids = {x['id'] for x in resp.data['results']}
        assert expected_ids == obtained_ids

    def test_lead_filter_with_entries_filter(self):
        project = self.create_project()
        lead1 = self.create(Lead, project=project, title='mytext')
        lead2 = self.create(Lead, project=project, source_raw='thisis_mytext')
        lead3 = self.create(Lead, project=project)

        url = '/api/v1/leads/filter/'
        post_data = {}
        self.authenticate()
        response = self.client.post(url, post_data)
        assert response.json()['count'] == 3

        post_data = {'custom_filters': LeadFilterSet.CustomFilter.EXCLUDE_EMPTY_FILTERED_ENTRIES}
        response = self.client.post(url, post_data)
        assert response.json()['count'] == 0, 'There are not supposed to be leads with entries'

        entry1 = self.create(Entry, project=project, lead=lead1, controlled=True, entry_type=Entry.TagType.EXCERPT)
        self.create(Entry, project=project, lead=lead1, controlled=True, entry_type=Entry.TagType.EXCERPT)

        post_data = {'entries_filter': [('controlled', True)]}
        response = self.client.post(url, post_data)
        assert response.json()['count'] == 3
        assert set([each['filteredEntriesCount'] for each in response.json()['results']]) \
            == set([0, 0, 2]), \
            response.json()

        entry2 = self.create(Entry, project=project, lead=lead2, controlled=False, entry_type=Entry.TagType.IMAGE)
        self.create(Entry, project=project, lead=lead3, controlled=False, entry_type=Entry.TagType.DATA_SERIES)
        post_data = {
            'custom_filters': LeadFilterSet.CustomFilter.EXCLUDE_EMPTY_FILTERED_ENTRIES,
            'entries_filter': [('controlled', True)]
        }
        response = self.client.post(url, post_data)
        assert response.json()['count'] == 1
        assert response.data['results'][0]['id'] == lead1.id, response.data
        assert response.json()['results'][0]['filteredEntriesCount'] == 2, response.json()

        post_data['entries_filter'] = []
        post_data['entries_filter'].append(('entry_type', [Entry.TagType.EXCERPT, Entry.TagType.IMAGE]))
        response = self.client.post(url, post_data)
        self.assertEqual(response.json()['count'], 2, response.json())
        # there should be 1 image entry and 2 excerpt entries
        assert set([1, 2]) == set([item['filteredEntriesCount'] for item in response.json()['results']]), response.json()

        # filter by project_entry_labels
        # Labels
        label1 = self.create(ProjectEntryLabel, project=project, title='Label 1', order=1, color='#23f23a')
        label2 = self.create(ProjectEntryLabel, project=project, title='Label 2', order=2, color='#23f23a')
        self.create(ProjectEntryLabel, project=project, title='Label 3', order=3, color='#23f23a')

        # Groups
        group11 = self.create(LeadEntryGroup, lead=lead1, title='Group 1', order=1)
        group12 = self.create(LeadEntryGroup, lead=lead1, title='Group 2', order=2)
        group21 = self.create(LeadEntryGroup, lead=lead2, title='Group 2', order=2)

        self.create(EntryGroupLabel, group=group11, label=label1, entry=entry1)
        self.create(EntryGroupLabel, group=group12, label=label2, entry=entry1)
        self.create(EntryGroupLabel, group=group21, label=label2, entry=entry2)

        post_data['entries_filter'] = []
        post_data['entries_filter'].append(('project_entry_labels', [label1.id]))
        response = self.client.post(url, post_data)
        self.assertEqual(response.json()['count'], 1, response.json())
        assert response.json()['results'][0]['filteredEntriesCount'] == 1, response.json()

        post_data['entries_filter'] = []
        post_data['entries_filter'].append(('project_entry_labels', [label1.id, label2.id]))
        response = self.client.post(url, post_data)
        self.assertEqual(response.json()['count'], 2, response.json())
        # lead1 has 1 label1+label2 entries
        # lead2 has 1 label2 entries
        assert [1, 1] == [item['filteredEntriesCount'] for item in response.json()['results']], response.json()

    def test_filtered_lead_list_with_controlled_entries_count(self):
        project = self.create_project()

        lead = self.create(Lead, project=project)
        lead2 = self.create(Lead, project=project)
        self.create_entry(lead=lead, project=project, controlled=True)
        self.create_entry(lead=lead, project=project, controlled=False)
        self.create_entry(lead=lead2, project=project, controlled=True)

        url = '/api/v1/leads/filter/'
        self.authenticate()
        resp = self.client.post(url, dict())
        self.assert_200(resp)
        counts = [x['controlled_entries_count'] for x in resp.data['results']]
        self.assertEqual(counts, [1, 1])

    def test_lead_filter_search_by_author(self):
        project = self.create_project()
        author = self.create(Organization, title='blablaone')
        author2 = self.create(Organization, title='blablatwo')

        lead1 = self.create(Lead, project=project, author=author, author_raw='wood')
        lead2 = self.create(Lead, project=project, author=author2)
        self.create(Lead, project=project, author=None)

        lead = self.create(Lead, project=project)
        lead.authors.set([author, author2])

        url = '/api/v1/leads/filter/'
        post_data = {'search': 'blablaone'}
        expected_ids = {lead1.id, lead.id}
        self.authenticate()
        resp = self.client.post(url, post_data)
        self.assert_200(resp)
        obtained_ids = {x['id'] for x in resp.data['results']}
        assert expected_ids == obtained_ids

        post_data = {'search': 'blablatwo'}
        expected_ids = {lead2.id, lead.id}
        resp = self.client.post(url, post_data)
        self.assert_200(resp)
        obtained_ids = {x['id'] for x in resp.data['results']}
        assert expected_ids == obtained_ids

        post_data = {'search': 'wood'}
        expected_ids = {lead1.id}
        resp = self.client.post(url, post_data)
        self.assert_200(resp)
        obtained_ids = {x['id'] for x in resp.data['results']}
        assert expected_ids == obtained_ids

    def test_lead_filter_emm_entities(self):
        url = '/api/v1/leads/?emm_entities={}'
        project = self.create_project()

        # Create Entities
        entity1 = self.create(EMMEntity, name='entity1')
        entity2 = self.create(EMMEntity, name='entity2')
        entity3 = self.create(EMMEntity, name='entity3')
        entity4 = self.create(EMMEntity, name='entity4')  # noqa:F841

        lead1 = self.create_lead(project=project, emm_entities=[entity1])
        lead2 = self.create_lead(project=project, emm_entities=[entity2, entity3])
        lead3 = self.create_lead(project=project, emm_entities=[entity2])
        self.create_lead(project=project)

        def _test_response(resp):
            self.assert_200(resp)
            assert len(resp.data['results']) == 3, 'There should be three leads'
            ids_list = [x['id']for x in resp.data['results']]
            assert lead1.id in ids_list
            assert lead2.id in ids_list
            assert lead3.id in ids_list

        # Test get filter
        self.authenticate()
        # Get a single lead
        resp = self.client.get(url.format(entity1.id))
        self.assert_200(resp)
        assert len(resp.data['results']) == 1, 'There should be one lead'
        assert resp.data['results'][0]['id'] == lead1.id

        # Get a multiple leads
        entities_query = ','.join([str(entity1.id), str(entity2.id)])
        resp = self.client.get(url.format(entities_query))
        _test_response(resp)

        # test post filter
        url = '/api/v1/leads/filter/'
        filter_data = {'emm_entities': [entity1.id]}
        self.authenticate()
        resp = self.client.post(url, filter_data, format='json')
        assert len(resp.data['results']) == 1, 'There should be one lead'
        assert resp.data['results'][0]['id'] == lead1.id

        filter_data = {'emm_entities': [entity1.id, entity2.id]}
        self.authenticate()
        resp = self.client.post(url, filter_data, format='json')

        _test_response(resp)

    def test_lead_filter_emm_keywords(self):
        url = '/api/v1/leads/?emm_keywords={}'
        project = self.create_project()

        lead1 = self.create_lead(project=project)
        lead2 = self.create_lead(project=project)
        lead3 = self.create_lead(project=project)
        lead4 = self.create_lead(project=project)

        # Create LeadEMMTrigger objects with
        self.create(
            LeadEMMTrigger, lead=lead1, count=5,
            emm_keyword='keyword1', emm_risk_factor='rf1',
        )
        self.create(
            LeadEMMTrigger, lead=lead2, count=3,
            emm_keyword='keyword1', emm_risk_factor='rf2',
        )
        self.create(
            LeadEMMTrigger, lead=lead3, count=3,
            emm_keyword='keyword3', emm_risk_factor='rf2',
        )
        self.create(
            LeadEMMTrigger, lead=lead4, count=3,
            emm_keyword='keyword2', emm_risk_factor='rf1',
        )

        self.authenticate()

        # Get a single lead
        resp = self.client.get(url.format('keyword1'))
        self.assert_200(resp)
        assert len(resp.data['results']) == 2, 'There should be 2 leads'
        ids_list = [x['id']for x in resp.data['results']]
        assert lead1.id in ids_list
        assert lead2.id in ids_list

        # Get multiple leads
        entities_query = ','.join(['keyword1', 'keyword2'])
        resp = self.client.get(url.format(entities_query))
        self.assert_200(resp)
        assert len(resp.data['results']) == 3, 'There should be three leads'
        ids_list = [x['id']for x in resp.data['results']]
        assert lead1.id in ids_list
        assert lead2.id in ids_list
        assert lead4.id in ids_list

    def test_lead_filter_emm_risk_factors(self):
        url = '/api/v1/leads/?emm_risk_factors={}'
        project = self.create_project()

        lead1 = self.create_lead(project=project)
        lead2 = self.create_lead(project=project)
        lead3 = self.create_lead(project=project)
        lead4 = self.create_lead(project=project)

        # Create LeadEMMTrigger objects with
        self.create(
            LeadEMMTrigger, lead=lead1, count=5,
            emm_keyword='keyword1', emm_risk_factor='rf1',
        )
        self.create(
            LeadEMMTrigger, lead=lead2, count=3,
            emm_keyword='keyword1', emm_risk_factor='rf2',
        )
        self.create(
            LeadEMMTrigger, lead=lead3, count=3,
            emm_keyword='keyword3', emm_risk_factor='rf2',
        )
        self.create(
            LeadEMMTrigger, lead=lead4, count=3,
            emm_keyword='keyword2', emm_risk_factor='rf1',
        )

        self.authenticate()

        # Get a single lead
        resp = self.client.get(url.format('rf1'))
        self.assert_200(resp)
        assert len(resp.data['results']) == 2, 'There should be 2 leads'
        ids_list = [x['id']for x in resp.data['results']]
        assert lead1.id in ids_list
        assert lead4.id in ids_list

        # Get multiple leads
        entities_query = ','.join(['rf1', 'rf2'])
        resp = self.client.get(url.format(entities_query))
        self.assert_200(resp)
        assert len(resp.data['results']) == 4, 'There should be four leads'
        ids_list = [x['id'] for x in resp.data['results']]
        assert lead1.id in ids_list
        assert lead2.id in ids_list
        assert lead3.id in ids_list
        assert lead4.id in ids_list

    def test_get_emm_extra_with_emm_entities_filter(self):
        url = '/api/v1/leads/emm-summary/?emm_entities={}'
        project = self.create_project()

        # Create Entities
        entity1 = self.create(EMMEntity, name='entity1')
        entity2 = self.create(EMMEntity, name='entity2')
        entity3 = self.create(EMMEntity, name='entity3')
        entity4 = self.create(EMMEntity, name='entity4')  # noqa:F841

        self.create_lead(project=project, emm_entities=[entity1])
        self.create_lead(project=project, emm_entities=[entity2, entity3])
        self.create_lead(project=project, emm_entities=[entity2])
        self.create_lead(project=project)

        # Test get filter
        self.authenticate()
        # Get a single lead
        entities_query = ','.join([str(entity1.id), str(entity2.id)])
        resp = self.client.get(url.format(entities_query))
        self.assert_200(resp)

        extra = resp.data
        assert 'emm_entities' in extra
        assert 'emm_triggers' in extra

        expected_entities_counts = {('entity1', 1), ('entity2', 2), ('entity3', 1)}
        result_entities_counts = {(x['name'], x['total_count']) for x in extra['emm_entities']}
        assert expected_entities_counts == result_entities_counts

        # TODO: test post
        filter_data = {'emm_entities': [entity1.id, entity2.id]}
        url = '/api/v1/leads/emm-summary/'

        self.authenticate()
        self.client.post(url, data=filter_data, format='json')
        self.assert_200(resp)

        extra = resp.data
        assert 'emm_entities' in extra
        assert 'emm_triggers' in extra

        expected_entities_counts = {('entity1', 1), ('entity2', 2), ('entity3', 1)}
        result_entities_counts = {(x['name'], x['total_count']) for x in extra['emm_entities']}
        assert expected_entities_counts == result_entities_counts

    def test_get_emm_extra_with_emm_keywords_filter(self):
        project = self.create_project()

        lead1 = self.create_lead(project=project)
        lead2 = self.create_lead(project=project)
        lead3 = self.create_lead(project=project)
        lead4 = self.create_lead(project=project)

        # Create LeadEMMTrigger objects with
        self.create(
            LeadEMMTrigger, lead=lead1, count=5,
            emm_keyword='keyword1', emm_risk_factor='rf1',
        )
        self.create(
            LeadEMMTrigger, lead=lead2, count=3,
            emm_keyword='keyword1', emm_risk_factor='rf1',
        )
        self.create(
            LeadEMMTrigger, lead=lead3, count=3,
            emm_keyword='keyword3', emm_risk_factor='rf2',
        )
        self.create(
            LeadEMMTrigger, lead=lead4, count=3,
            emm_keyword='keyword2', emm_risk_factor='rf2',
        )

        # Test GET
        url = '/api/v1/leads/emm-summary/?emm_keywords=keyword1,keyword2'
        self.authenticate()
        resp = self.client.get(url)
        self.assert_200(resp)

        data = resp.data
        assert 'emm_entities' in data
        assert 'emm_triggers' in data

        expected_triggers = {('keyword1', 'rf1', 8), ('keyword2', 'rf2', 3)}
        result_triggers = {
            (x['emm_keyword'], x['emm_risk_factor'], x['total_count'])
            for x in data['emm_triggers']
        }
        assert expected_triggers == result_triggers

    def test_lead_summary_get(self):
        lead1 = self.create_lead()
        lead2 = self.create_lead()
        self.create_entry(lead=lead1)
        self.create_entry(lead=lead1, controlled=True)
        self.create_entry(lead=lead2)

        url = '/api/v1/leads/summary/'
        self.authenticate()
        resp = self.client.get(url)
        self.assert_200(resp)

        self.assertEqual(resp.data['total'], 2)
        self.assertEqual(resp.data['total_entries'], 3)
        self.assertEqual(resp.data['total_controlled_entries'], 1)
        self.assertEqual(resp.data['total_uncontrolled_entries'], 2)
        assert 'emm_entities' in resp.data
        assert 'emm_triggers' in resp.data

    def test_lead_summary_post(self):
        lead1 = self.create_lead()
        lead2 = self.create_lead()
        self.create_entry(lead=lead1)
        self.create_entry(lead=lead1, controlled=True)
        self.create_entry(lead=lead2)

        url = '/api/v1/leads/summary/'
        self.authenticate()
        resp = self.client.post(url, data={}, format='json')
        self.assert_200(resp)

        self.assertEqual(resp.data['total'], 2)
        self.assertEqual(resp.data['total_entries'], 3)
        self.assertEqual(resp.data['total_controlled_entries'], 1)
        self.assertEqual(resp.data['total_uncontrolled_entries'], 2)
        assert 'emm_entities' in resp.data
        assert 'emm_triggers' in resp.data

    def test_lead_group_post(self):
        project = self.create_project()
        data = {
            'project': project.id,
            'title': 'Test Lead Group Title'
        }
        url = '/api/v1/lead-groups/'
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['project'], data['project'])

    def test_lead_group_get(self):
        project_1 = self.create_project()
        project_2 = self.create_project()
        leadg_1 = self.create(LeadGroup, project=project_1, title='test1')
        leadg_2 = self.create(LeadGroup, project=project_1, title='test2')
        self.create(LeadGroup, project=project_2, title='test3')
        self.create(LeadGroup, project=project_2, title='test4')

        url = '/api/v1/lead-groups/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data), 4)

        # test for project filter
        url = f'/api/v1/lead-groups/?project={project_1.id}'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(
            set(lg['id'] for lg in response.data['results']),
            set([leadg_1.id, leadg_2.id])
        )

        # test for the search field `title`
        url = '/api/v1/lead-groups/?search=test1'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], leadg_1.id)

    def test_authors_and_authoring_organization_type(self):
        project = self.create_project(title='lead_test_project')
        organization_type1 = self.create(OrganizationType, title='National')
        organization_type2 = self.create(OrganizationType, title='International')
        organization_type3 = self.create(OrganizationType, title='Government')

        organization1 = self.create(Organization, organization_type=organization_type1)
        organization2 = self.create(Organization, organization_type=organization_type2)
        organization3 = self.create(Organization, organization_type=organization_type3)
        organization4 = self.create(Organization, parent=organization1)
        organization5 = self.create(Organization, organization_type=organization_type1)
        # organization without organization_type
        organization6 = self.create(Organization)

        # create lead
        lead1 = self.create_lead(project=project, authors=[organization3, organization2])
        lead2 = self.create_lead(project=project, authors=[organization4])
        # just provide author for this
        lead3 = self.create_lead(project=project, author=organization1)
        # lead that have authors with same organization_type
        lead4 = self.create_lead(project=project, authors=[organization5, organization1])
        lead5 = self.create_lead(project=project, authors=[organization6])
        # test for authors
        self.assertEqual(
            set(lead1.get_authors_display()),
            set(','.join([organization2.title, organization3.title]))
        )
        self.assertEqual(
            lead2.get_authors_display(),
            organization1.title  # organization1 since lead2 authors have parent
        )
        self.assertEqual(
            lead3.get_authors_display(),
            organization1.title
        )
        self.assertEqual(
            set(lead4.get_authors_display()),
            set(','.join([organization1.title, organization5.title]))
        )
        # test for authoring_oragnizations_type
        self.assertEqual(
            set(lead1.get_authoring_organizations_type_display()),
            set(','.join([organization_type2.title, organization_type3.title]))
        )
        self.assertEqual(
            lead2.get_authoring_organizations_type_display(),
            organization_type1.title  # organization_type1 since lead2 authors have parent
        )
        self.assertEqual(
            lead3.get_authoring_organizations_type_display(),
            organization_type1.title
        )
        self.assertEqual(
            lead4.get_authoring_organizations_type_display(),
            organization_type1.title  # organization_type1 since both authors have same organization_type
        )
        self.assertEqual(
            lead5.get_authoring_organizations_type_display(),
            ''
        )

    def test_is_assessment_lead(self):
        project = self.create_project()
        lead = self.create(
            Lead,
            project=project,
            is_assessment_lead=True
        )

        url = f'/api/v1/leads/{lead.id}/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        # now create Assessment for the lead
        self.create(Assessment, lead=lead)
        data = {
            'is_assessment_lead': False
        }
        url = f'/api/v1/leads/{lead.id}/'
        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_400(response)
        self.assertEqual(
            response.data['errors']['is_assessment_lead'],
            [ErrorDetail(string='Lead already has an assessment.', code='invalid')]
        )

        # here delete the assessment that has lead
        Assessment.objects.filter(lead=lead).delete()
        data = {
            'is_assessment_lead': False
        }
        url = f'/api/v1/leads/{lead.id}/'
        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_200(response)

# Data to use for testing web info extractor
# Including, url of the page and its attributes:
# source, country, date, website

SAMPLE_WEB_INFO_URL = 'https://reliefweb.int/report/yemen/yemen-emergency-food-security-and-nutrition-assessment-efsna-2016-preliminary-results' # noqa
SAMPLE_WEB_INFO_SOURCE = 'World Food Programme, UN Children\'s Fund, Food and Agriculture Organization of the United Nations' # noqa
SAMPLE_WEB_INFO_COUNTRY = 'Yemen'
SAMPLE_WEB_INFO_DATE = date(2017, 1, 26)
SAMPLE_WEB_INFO_TITLE = 'Yemen Emergency Food Security and Nutrition Assessment (EFSNA) 2016 - Preliminary Results' # noqa


class WebInfoExtractionTests(TestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.reliefweb = self.create(Organization, **RELIEFWEB_DATA)
        self.redhum = self.create(Organization, **REDHUM_DATA)
        self.unhcr = self.create(Organization, **UNHCR_DATA)

    def test_redhum(self):
        url = '/api/v1/web-info-extract/'
        data = {
            'url': 'https://redhum.org/documento/3227553',
        }
        try:
            self.authenticate()
            response = self.client.post(url, data)
            rdata = self.client.post(url, data).data
            self.assert_200(response)
            self.assertEqual(rdata['title'], 'Pregnant women flee lack of maternal health care in Venezuela')
            self.assertEqual(rdata['date'], '2019-07-23')
            self.assertEqual(rdata['country'], 'Colombia')
            self.assertEqual(rdata['url'], data['url'])
            self.assertEqual(rdata['source_raw'], 'redhum')
            self.assertEqual(rdata['author_raw'], 'United Nations High Commissioner for Refugees')
            self.assertEqual(rdata['source'], SimpleOrganizationSerializer(self.redhum).data)
            self.assertEqual(rdata['author'], SimpleOrganizationSerializer(self.unhcr).data)
        except Exception:
            import traceback
            logger.warning('\n' + ('*' * 30))
            logger.warning('LEAD WEB INFO EXTRACTION ERROR:')
            logger.warning(traceback.format_exc())
            return

    def test_extract_web_info(self):
        # Create a sample project containing the sample country
        sample_region = self.create(Region, title=SAMPLE_WEB_INFO_COUNTRY,
                                    public=True)
        sample_project = self.create(Project, role=self.admin_role)
        sample_project.regions.add(sample_region)

        url = '/api/v1/web-info-extract/'
        data = {
            'url': SAMPLE_WEB_INFO_URL
        }

        try:
            self.authenticate()
            response = self.client.post(url, data)
            self.assert_200(response)
        except Exception:
            import traceback
            logger.warning('\n' + ('*' * 30))
            logger.warning('LEAD WEB INFO EXTRACTION ERROR:')
            logger.warning(traceback.format_exc())
            return

        expected = {
            'project': sample_project.id,
            'date': SAMPLE_WEB_INFO_DATE,
            'country': SAMPLE_WEB_INFO_COUNTRY,
            'title': SAMPLE_WEB_INFO_TITLE,
            'url': SAMPLE_WEB_INFO_URL,
            'source': SimpleOrganizationSerializer(self.reliefweb).data,
            'source_raw': 'reliefweb',
            'author': None,
            'author_raw': SAMPLE_WEB_INFO_SOURCE,
            'existing': False,
        }
        self.assertEqualWithWarning(expected, response.data)


class WebInfoDataTestCase(TestCase):
    def test_relief_web(self):
        self.create(Organization, title='Organization 1')
        self.create(Organization, title='Organization 2')

        url = '/api/v1/web-info-data/'
        data = {
            'url': SAMPLE_WEB_INFO_URL,
            'authors_raw': ['Organization1', 'Organization2'],
            'source_raw': 'Organization1'
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_200(response)


class TestExtractorCallback(TestCase):
    def setUp(self):
        super().setUp()
        self.lead = LeadFactory.create()

    @mock.patch('lead.serializers.index_lead_and_calculate_duplicates.delay')
    @mock.patch('deepl_integration.handlers.RequestHelper.get_text')
    @mock.patch('deepl_integration.handlers.RequestHelper.get_file')
    def test_extractor_callback_url(self, get_file_mock, get_text_mock, index_lead_func):
        url = '/api/v1/callback/lead-extract/'
        self.authenticate()

        image = SimpleUploadedFile(
            name='test_image.jpg', content=b'', content_type='image/jpeg'
        )
        get_file_mock.return_value = image
        get_text_mock.return_value = 'Extracted text'

        # Before callback
        lead_preview = LeadPreview.objects.filter(lead=self.lead).last()
        self.assertEqual(lead_preview, None)
        images_count = LeadPreview.objects.filter(lead=self.lead).count()
        self.assertEqual(images_count, 0)

        data = {
            'client_id': LeadExtractionHandler.get_client_id(self.lead),
            'images_path': [
                {
                    'page_number': 1,
                    'images': [
                        'http://random.com/image1.jpeg',
                        'http://random.com/image2.jpeg'
                    ],
                }
            ],
            'tables_path': [
                {
                    "page_number": 1,
                    "order": 0,
                    "image_link": "http://random.com/timetable.png",
                    "content_link": "http://random.com/table_timetable.xlsx"
                }
            ],
            'text_path': 'http://random.com/extracted_file.txt',
            'url': 'http://random.com/pdf_file.pdf',
            'total_words_count': 300,
            'total_pages': 4,
            'status': DeeplServerBaseCallbackSerializer.Status.FAILED.value,
            'text_extraction_id': '00431349-5879-4d59-9827-0b12491c4baa'
        }

        # After callback [Failure]
        response = self.client.post(url, data)
        self.assert_200(response)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.extraction_status, Lead.ExtractionStatus.FAILED)
        self.assertEqual(LeadPreview.objects.filter(lead=self.lead).count(), 0)
        self.assertEqual(LeadPreviewAttachment.objects.filter(lead=self.lead).count(), 0)

        data['status'] = DeeplServerBaseCallbackSerializer.Status.SUCCESS.value
        # After callback [Success]
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, data)
        self.assert_200(response)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.extraction_status, Lead.ExtractionStatus.SUCCESS)
        self.assertEqual(LeadPreview.objects.filter(lead=self.lead).count(), 1)
        lead_preview = LeadPreview.objects.filter(lead=self.lead).last()
        self.assertEqual(lead_preview.text_extract, 'Extracted text')
        self.assertEqual(lead_preview.word_count, 300)
        self.assertEqual(lead_preview.page_count, 4)
        self.assertEqual(LeadPreviewAttachment.objects.filter(lead=self.lead).count(), 3)
        self.assertEqual(LeadPreviewAttachment.objects.filter(
            lead=self.lead, type=LeadPreviewAttachment.AttachmentFileType.IMAGE).count(), 2
        )

        index_lead_func.assert_called_once_with(self.lead.id)

    def test_client_id_generator(self):
        project = self.create_project()
        lead1 = self.create_lead(project=project)
        lead2 = self.create_lead(project=project)
        lead1_client_id = LeadExtractionHandler.get_client_id(lead1)
        lead2_client_id = LeadExtractionHandler.get_client_id(lead2)
        lead2.delete()
        for lead, client_id, excepted_exception in [
            (lead1, lead1_client_id, None),
            (
                lead1,
                f'{UidBase64Helper.encode(lead1.pk)}-some-random-id',
                LeadExtractionHandler.Exception.InvalidOrExpiredToken,
            ),
            (lead1, '11-some-random-id', LeadExtractionHandler.Exception.InvalidTokenValue),
            (lead1, 'some-random-id', LeadExtractionHandler.Exception.InvalidTokenValue),
            (lead2, lead2_client_id, LeadExtractionHandler.Exception.ObjectNotFound),
            (lead2, 'somerandomid', LeadExtractionHandler.Exception.InvalidTokenValue),
        ]:
            if excepted_exception:
                with self.assertRaises(excepted_exception):
                    LeadExtractionHandler.get_object_using_client_id(client_id)
            else:
                assert LeadExtractionHandler.get_object_using_client_id(client_id) == lead


class AutoEntryExtractionTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.lead = LeadFactory.create()
        self.lead_preview = LeadPreviewFactory.create(lead=self.lead, text_extraction_id=str(uuid.uuid1()))

    @mock.patch('deepl_integration.handlers.RequestHelper.json')
    def test_entry_extraction_callback_url(self, get_json_mock):
        url = '/api/v1/callback/auto-assisted-tagging-draft-entry-prediction/'
        self.authenticate()
        SAMPLE_AUTO_ASSISTED_TAGGING = {
            "metadata": {"total_pages": 10, "total_words_count": 5876},
            "blocks": [
                {
                    "type": "text",
                    "page": 1,
                    "text": "Entry-Text-1",
                    "textOrder": 1,
                    "relevant": True,
                    "prediction_status": True,
                    "geolocations": [
                        {
                            "entity": "Somalia",
                            "meta": {"offset_start": 88, "offset_end": 94, "latitude": -10, "longitude": -55},
                        }
                    ],
                    "classification": {"1": {"101": {"prediction": 2.70270529e-05, "threshold": 0.14, "is_selected": True}}},
                },
                {
                    "type": "text",
                    "page": 2,
                    "text": "Entry-Text-2",
                    "textOrder": 2,
                    "relevant": True,
                    "prediction_status": True,
                    "geolocations": [
                        {
                            "entity": "Nigeria",
                            "meta": {"offset_start": 183, "offset_end": 191, "latitude": None, "longitude": None},
                        }
                    ],
                    "classification": {
                        "1": {"101": {"prediction": 2.0000270270529, "threshold": 0.14, "is_selected": True}}
                    },
                },
                {
                    "type": "text",
                    "page": 3,
                    "text": "This is a non-relevant text",
                    "textOrder": 3,
                    "relevant": False,
                    "prediction_status": False,
                    "geolocations": [],
                    "classification": {},
                },
            ],
            "classification_model_info": {"name": "all_tags_model", "version": "1.0.0"},
            "client_id": AutoAssistedTaggingDraftEntryHandler.get_client_id(self.lead),
            "entry_extraction_id": "73f9ca13-deb2-4f39-8e86-a856490bfc0d",
            "text_extraction_id": str(self.lead_preview.text_extraction_id),
        }
        get_json_mock.return_value = SAMPLE_AUTO_ASSISTED_TAGGING

        # Invalid clientId
        data = {
            'client_id': 'invalid-client-id',
            'entry_extraction_classification_path': 'https://random-domain.com/random-url.json',
            'text_extraction_id': str(self.lead_preview.text_extraction_id),
            'status': 1
        }
        response = self.client.post(url, data)
        self.assert_400(response)

        # valid ClientID
        data['client_id'] = AutoAssistedTaggingDraftEntryHandler.get_client_id(self.lead)
        response = self.client.post(url, data)
        self.assert_200(response)
        self.lead.refresh_from_db()
        self.assertEqual(str(LeadPreview.objects.get(lead=self.lead).text_extraction_id), data['text_extraction_id'])
        self.assertEqual(self.lead.auto_entry_extraction_status, Lead.AutoExtractionStatus.SUCCESS)
