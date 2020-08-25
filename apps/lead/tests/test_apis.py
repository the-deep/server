from deep.tests import (
    TestCase,
    mock_module_function_with_return_value
)
from user.models import User
from user.serializers import SimpleUserSerializer
from project.models import (
    Project, ProjectMembership,
    ProjectUserGroupMembership,
)
from project.serializers import SimpleProjectSerializer
from geo.models import Region

from organization.models import Organization
from organization.serializers import SimpleOrganizationSerializer
from lead.filter_set import LeadFilterSet
from lead.serializers import SimpleLeadGroupSerializer
from lead.models import (
    Lead,
    LeadPreview,
    LeadPreviewImage,
    EMMEntity,
    LeadEMMTrigger,
    LeadGroup,
)
from lead.tasks import LeadDuplicationInfo
from user_group.models import UserGroup, GroupMembership

import logging
from datetime import date

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

get_duplicate_decorator = mock_module_function_with_return_value(
    'lead.serializers.get_duplicate_leads',
    LeadDuplicationInfo(similar_leads=[])
)
# NOTE that no need to mock add_to_index because that is called only when the get_duplicate_leads
# return object has attribute 'vector' set. In above mock, it will have a default value None


class LeadTests(TestCase):
    def setUp(self):
        super().setUp()
        self.author = self.source = self.create_organization()

    def create_organization(self, **kwargs):
        return self.create(Organization, **kwargs)

    @get_duplicate_decorator
    def test_create_lead(self, assignee=None):
        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
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
        self.assertEqual(r_data['priority'], Lead.LOW)

    @get_duplicate_decorator
    def test_create_high_priority_lead(self, assignee=None):
        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': assignee or self.user.id,
            'priority': Lead.HIGH,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Lead.objects.count(), lead_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['assignee'], self.user.id)

        # low is default priority
        self.assertEqual(r_data['priority'], Lead.HIGH)

    @get_duplicate_decorator
    def test_create_lead_with_emm(self):
        entity1 = self.create(EMMEntity, name='entity1')
        entity2 = self.create(EMMEntity, name='entity2')

        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

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

    @get_duplicate_decorator
    def test_get_lead_check_no_of_entries(self, assignee=None):
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': assignee or self.user.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        url = '/api/v1/leads/'

        response = self.client.get(url)

        r_data = response.json()
        assert 'noOfEntries' in r_data["results"][0]

    @get_duplicate_decorator
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
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
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
                {'key': c[0], 'value': c[1]} for c in Lead.CONFIDENTIALITIES
            ],
            'status': [
                {'key': s[0], 'value': s[1]} for s in Lead.STATUSES
            ],
            'priority': [
                {'key': s[0], 'value': s[1]} for s in Lead.PRIORITIES
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
        assert not rdata['has_emm_leads'], "There should be no emm leads in the project"
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
            "projects": [project.id],
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
        assert data['has_emm_leads'], "There are emm leads"

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
        assert not data['emm_entities'], "Entities not specified."

        # Check emm_risk_factors
        assert 'emm_risk_factors' in data
        expected_risk_factors_count_set = {('rf1', 'rf1', 8)}
        result_risk_factors_count_set = {(x['key'], x['label'], x['total_count']) for x in data['emm_risk_factors']}
        assert expected_risk_factors_count_set == result_risk_factors_count_set

        # Check emm_keywords
        assert 'emm_keywords' in data
        assert not data['emm_entities'], "Keywords not specified."

        assert 'has_emm_leads' in data
        assert data['has_emm_leads'], "There are emm leads"

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
        assert data['has_emm_leads'], "There are emm leads"

        # Now check options for project1, there should be no emm related data
        url = f'/api/v1/lead-options/?projects={project1.id}'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data

        assert 'has_emm_leads' in data
        assert not data['has_emm_leads'], "this Project should not have emm"
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
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
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

        assert leads_count == Lead.objects.all().count(), "No new lead should have been created"

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
        emm_keyword = 'emm1'
        emm_risk_factor = 'risk1'
        emm_count = 22
        emm_entity_name = 'emm_entity_11'

        # Generate Leads
        lead1 = self.create(
            Lead, title=lead1_title, project=project1s, source_type=Lead.WEBSITE, url='http://example.com')
        lead2 = self.create(Lead, project=project2s)
        lead3 = self.create(Lead, project=project3s)
        lead4 = self.create(Lead, project=project4s)

        # For duplicate url validation check
        self.create(Lead, title=lead1_title, project=project2d, source_type=Lead.WEBSITE, url='http://example.com')

        # Generating Foreign elements for lead1
        self.create(LeadPreview, lead=lead1, text_extract=lead1_text_extract)
        self.create(LeadPreviewImage, lead=lead1, file=lead1_preview_file)
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
        lead1_copy = Lead.objects.filter(title=lead1_title).exclude(pk=lead1.pk).first()
        emm_trigger = lead1_copy.emm_triggers.filter(emm_risk_factor=emm_risk_factor, emm_keyword=emm_keyword)[0]
        assert lead1_copy.pk != lead1.pk
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
            'source_type': Lead.DISK,
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
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
            'source_type': Lead.TEXT,
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
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

        self.create_lead(project=project, priority=Lead.HIGH)
        self.create_lead(project=project, priority=Lead.MEDIUM)
        self.create_lead(project=project, priority=Lead.HIGH)
        self.create_lead(project=project, priority=Lead.LOW)

        url = '/api/v1/leads/?ordering=priority'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        leads = response.data['results']
        assert leads[0]['priority'] == Lead.LOW
        assert leads[1]['priority'] == Lead.MEDIUM
        assert leads[2]['priority'] == Lead.HIGH
        assert leads[3]['priority'] == Lead.HIGH

        url = '/api/v1/leads/?ordering=-priority'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        leads = response.data['results']
        assert leads[0]['priority'] == Lead.HIGH
        assert leads[1]['priority'] == Lead.HIGH
        assert leads[2]['priority'] == Lead.MEDIUM
        assert leads[3]['priority'] == Lead.LOW

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
        assert len(response.data['results']) == 3, "Three leads created"
        leads = response.data['results']
        assert leads[0]['id'] == lead3.id, "Preview3 has no pages"
        assert leads[1]['id'] == lead2.id, "Preview2 has less pages"
        assert leads[2]['id'] == lead1.id, "Preview1 has more pages"

        # Descending ordering
        url = '/api/v1/leads/?ordering=,-page_count,,'  # this also tests leading/trailing/multiple commas
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        assert len(response.data['results']) == 3, "Three leads created"
        leads = response.data['results']
        assert leads[0]['id'] == lead1.id, "Preview1 has more pages"
        assert leads[1]['id'] == lead2.id, "Preview2 has less pages"
        assert leads[2]['id'] == lead3.id, "Preview3 has no pages"

    def test_lead_filter(self):
        project = self.create_project(create_assessment_template=True)
        project2 = self.create_project(create_assessment_template=True)

        lead1 = self.create_lead(project=project)
        lead2 = self.create_lead(project=project)
        lead3 = self.create_lead(project=project)
        lead4 = self.create_lead(project=project2, priority=Lead.HIGH)

        self.authenticate()

        response = self.client.get(f'/api/v1/leads/?project={project2.pk}&priority={Lead.HIGH}')
        assert response.json()['results'][0]['id'] == lead4.pk

        url = f'/api/v1/leads/?project={project.pk}'

        # Project filter test
        response = self.client.get(url)
        assert response.json()['count'] == 3, 'Lead count should be 3'

        # Entries exists filter test
        self.create_entry(lead=lead1)
        self.create_entry(lead=lead2)
        response = self.client.get(f'{url}&exists={LeadFilterSet.ENTRIES_EXIST}')
        assert response.json()['count'] == 2, 'Lead count should be 2 for lead with entries'

        # Entries do not exist filter test
        response = self.client.get(f'{url}&exists={LeadFilterSet.ENTRIES_DO_NOT_EXIST}')
        assert response.json()['count'] == 1, 'Lead count should be 1 for lead without entries'

        # Assessment exists filter test
        self.create_assessment(lead=lead1)
        self.create_assessment(lead=lead3)
        response = self.client.get(f'{url}&exists={LeadFilterSet.ASSESSMENT_EXISTS}')
        assert response.json()['count'] == 2, 'Lead count should be 2 for lead with assessment'

        # Assessment does not exist filter test
        response = self.client.get(f'{url}&exists={LeadFilterSet.ASSESSMENT_DOES_NOT_EXIST}')
        assert response.json()['count'] == 1, 'Lead count should be 1 for lead without assessment'

    def test_lead_filter_search(self):
        url = '/api/v1/leads/?emm_entities={}'
        project = self.create_project()
        lead1 = self.create(Lead, project=project, title='mytext')
        lead2 = self.create(Lead, project=project, source_raw='thisis_mytext')
        lead3 = self.create(Lead, project=project, website='http://thisis-mytext.com')
        self.create(Lead, project=project, title='nothing_here')

        url = '/api/v1/leads/?search={}'
        self.authenticate()
        resp = self.client.get(url.format('mytext'))
        self.assert_200(resp)

        expected_ids = {lead1.id, lead2.id, lead3.id}
        obtained_ids = {x['id'] for x in resp.data['results']}
        assert expected_ids == obtained_ids

        url = '/api/v1/leads/filter/'
        post_data = {'search': 'mytext'}
        self.authenticate()
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
            assert len(resp.data['results']) == 3, "There should be three leads"
            ids_list = [x['id']for x in resp.data['results']]
            assert lead1.id in ids_list
            assert lead2.id in ids_list
            assert lead3.id in ids_list

        # Test get filter
        self.authenticate()
        # Get a single lead
        resp = self.client.get(url.format(entity1.id))
        self.assert_200(resp)
        assert len(resp.data['results']) == 1, "There should be one lead"
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
        assert len(resp.data['results']) == 1, "There should be one lead"
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
        assert len(resp.data['results']) == 2, "There should be 2 leads"
        ids_list = [x['id']for x in resp.data['results']]
        assert lead1.id in ids_list
        assert lead2.id in ids_list

        # Get multiple leads
        entities_query = ','.join(['keyword1', 'keyword2'])
        resp = self.client.get(url.format(entities_query))
        self.assert_200(resp)
        assert len(resp.data['results']) == 3, "There should be three leads"
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
        assert len(resp.data['results']) == 2, "There should be 2 leads"
        ids_list = [x['id']for x in resp.data['results']]
        assert lead1.id in ids_list
        assert lead4.id in ids_list

        # Get multiple leads
        entities_query = ','.join(['rf1', 'rf2'])
        resp = self.client.get(url.format(entities_query))
        self.assert_200(resp)
        assert len(resp.data['results']) == 4, "There should be four leads"
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

# Data to use for testing web info extractor
# Including, url of the page and its attributes:
# source, country, date, website

SAMPLE_WEB_INFO_URL = 'https://reliefweb.int/report/yemen/yemen-emergency-food-security-and-nutrition-assessment-efsna-2016-preliminary-results' # noqa
SAMPLE_WEB_INFO_SOURCE = 'World Food Programme, UN Children\'s Fund, Food and Agriculture Organization of the United Nations' # noqa
SAMPLE_WEB_INFO_COUNTRY = 'Yemen'
SAMPLE_WEB_INFO_DATE = date(2017, 1, 26)
SAMPLE_WEB_INFO_WEBSITE = 'reliefweb.int'
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
            self.assertEqual(rdata['website'], 'redhum.org')
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
            'website': SAMPLE_WEB_INFO_WEBSITE,
            'title': SAMPLE_WEB_INFO_TITLE,
            'url': SAMPLE_WEB_INFO_URL,
            'source': SimpleOrganizationSerializer(self.reliefweb).data,
            'source_raw': 'reliefweb',
            'author': None,
            'author_raw': SAMPLE_WEB_INFO_SOURCE,
            'existing': False,
        }
        self.assertEqualWithWarning(expected, response.data)
