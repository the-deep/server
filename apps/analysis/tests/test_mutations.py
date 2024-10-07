import os
import datetime
import json
from unittest import mock
from utils.graphene.tests import GraphQLTestCase

from deepl_integration.handlers import AnalysisAutomaticSummaryHandler
from deepl_integration.serializers import DeeplServerBaseCallbackSerializer

from commons.schema_snapshots import SnapshotQuery
from user.factories import UserFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from analysis.factories import (
    AnalysisFactory,
    AnalysisPillarFactory,
    AnalysisReportFactory,
    AnalysisReportUploadFactory,
)

from analysis.models import (
    TopicModel,
    TopicModelCluster,
    AutomaticSummary,
    AnalyticalStatementNGram,
    AnalyticalStatementGeoTask,
    AnalysisReportSnapshot,
)


class TestAnalysisNlpMutationSchema(GraphQLTestCase):
    factories_used = [
        UserFactory,
        ProjectFactory,
        LeadFactory,
        EntryFactory,
        AnalysisFrameworkFactory,
    ]

    ENABLE_NOW_PATCHER = True

    TRIGGER_TOPIC_MODEL = '''
        mutation MyMutation ($projectId: ID!, $input: AnalysisTopicModelCreateInputType!) {
          project(id: $projectId) {
            triggerAnalysisTopicModel(data: $input) {
              ok
              errors
              result {
                id
                status
                clusters {
                  id
                  entries {
                    id
                    excerpt
                  }
                }
              }
            }
          }
        }
    '''

    QUERY_TOPIC_MODEL = '''
        query MyQuery ($projectId: ID!, $topicModelID: ID!) {
          project(id: $projectId) {
            analysisTopicModel(id: $topicModelID) {
              status
              id
              clusters {
                entries {
                  id
                  excerpt
                }
              }
            }
          }
        }
    '''

    TRIGGER_AUTOMATIC_SUMMARY = '''
        mutation MyMutation ($projectId: ID!, $input: AnalysisAutomaticSummaryCreateInputType!) {
          project(id: $projectId) {
            triggerAnalysisAutomaticSummary(data: $input) {
              ok
              errors
              result {
                id
                status
                summary
                informationGap
                analyticalStatement
              }
            }
          }
        }
    '''

    QUERY_AUTOMATIC_SUMMARY = '''
        query MyQuery ($projectId: ID!, $summaryID: ID!) {
          project(id: $projectId) {
            analysisAutomaticSummary(id: $summaryID) {
              id
              status
              summary
            }
          }
        }
    '''

    TRIGGER_AUTOMATIC_NGRAM = '''
        mutation MyMutation ($projectId: ID!, $input: AnalyticalStatementNGramCreateInputType!) {
          project(id: $projectId) {
            triggerAnalysisAutomaticNgram(data: $input) {
              ok
              errors
              result {
                id
                status
                unigrams {
                  word
                  count
                }
                bigrams {
                  word
                  count
                }
                trigrams {
                  word
                  count
                }
              }
            }
          }
        }
    '''

    QUERY_AUTOMATIC_NGRAM = '''
        query MyQuery ($projectId: ID!, $ngramID: ID!) {
          project(id: $projectId) {
            analysisAutomaticNgram(id: $ngramID) {
              id
              status
              unigrams {
                word
                count
              }
              bigrams {
                word
                count
              }
              trigrams {
                word
                count
              }
            }
          }
        }
    '''

    TRIGGER_GEOLOCATION = '''
        mutation MyMutation ($projectId: ID!, $input: AnalyticalStatementGeoTaskInputType!) {
          project(id: $projectId) {
            triggerAnalysisGeoLocation(data: $input) {
              errors
              ok
              result {
                id
                status
                entryGeo {
                  entryId
                  data {
                    meta {
                      latitude
                      longitude
                      offsetStart
                      offsetEnd
                    }
                    entity
                  }
                }
              }
            }
          }
        }
    '''

    QUERY_GEOLOCATION = '''
        query MyQuery ($projectId: ID!, $ID: ID!) {
          project(id: $projectId) {
            analysisGeoTask(id: $ID) {
              id
              status
              entryGeo {
                entryId
                data {
                  meta {
                    latitude
                    longitude
                    offsetStart
                    offsetEnd
                  }
                  entity
                }
              }
            }
          }
        }
    '''

    def setUp(self):
        super().setUp()
        self.af = AnalysisFrameworkFactory.create()
        self.project = ProjectFactory.create(analysis_framework=self.af)
        self.another_project = ProjectFactory.create()
        self.private_project = ProjectFactory.create(analysis_framework=self.af, is_private=True)
        # User with role
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.member_user = UserFactory.create()
        self.project.add_member(self.member_user, role=self.project_role_member)
        self.private_project.add_member(self.member_user, role=self.project_role_member)

    def _check_status(self, obj, status):
        obj.refresh_from_db()
        self.assertEqual(obj.status, status)

    @mock.patch('deepl_integration.handlers.RequestHelper')
    @mock.patch('deepl_integration.handlers.requests')
    def test_topic_model(self, trigger_results_mock, RequestHelperMock):
        analysis = AnalysisFactory.create(
            project=self.project,
            team_lead=self.member_user,
            end_date=datetime.date(2022, 4, 1),
        )
        analysis_pillar = AnalysisPillarFactory.create(
            analysis=analysis,
            assignee=self.member_user,
        )
        private_analysis = AnalysisFactory.create(
            project=self.private_project,
            team_lead=self.member_user,
            end_date=datetime.date(2022, 4, 1),
        )
        private_analysis_pillar = AnalysisPillarFactory.create(
            analysis=private_analysis,
            assignee=self.member_user,
        )

        # NOTE: This should be ignored by analysis end_date
        lead1 = LeadFactory.create(
            project=self.project,
            published_on=datetime.date(2022, 5, 1),
        )
        lead2 = LeadFactory.create(
            project=self.project,
            published_on=datetime.date(2022, 3, 30),
        )
        another_lead = LeadFactory.create(
            project=self.another_project,
            published_on=datetime.date(2022, 3, 30),
        )
        EntryFactory.create_batch(3, analysis_framework=self.af, lead=lead1)
        lead2_entries = EntryFactory.create_batch(4, analysis_framework=self.af, lead=lead2)
        EntryFactory.create_batch(4, analysis_framework=self.af, lead=another_lead)

        def nlp_validator_mock(url, data=None, json=None, **kwargs):
            if not json:
                return mock.MagicMock(status_code=500)

            # Get payload from file
            payload = self.get_json_media_file(
                json['entries_url'].split('http://testserver/media/')[1],
            )
            # TODO: Need to check the Child fields of data and File payload as well
            expected_keys = ['data', 'tags']
            if set(payload.keys()) != set(expected_keys):
                return mock.MagicMock(status_code=400)
            return mock.MagicMock(status_code=202)

        def nlp_fail_mock(*args, **kwargs):
            return mock.MagicMock(status_code=500)

        trigger_results_mock.post.side_effect = nlp_validator_mock

        def _mutation_check(minput, **kwargs):
            return self.query_check(
                self.TRIGGER_TOPIC_MODEL,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.project.id},
                **kwargs
            )

        def _private_project_mutation_check(minput, **kwargs):
            return self.query_check(
                self.TRIGGER_TOPIC_MODEL,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.private_project.id},
                **kwargs
            )

        def _query_check(_id):
            return self.query_check(
                self.QUERY_TOPIC_MODEL,
                minput=minput,
                variables={'projectId': self.project.id, 'topicModelID': _id},
            )

        minput = dict(
            analysisPillar='0',  # Non existing ID
            additionalFilters=dict(
                filterableData=[
                    dict(
                        filterKey='random-key',
                        value='random-value',
                    )
                ],
            ),
            widgetTags=[
                'tag1',
                'tag2',
            ],
        )

        # -- Without login
        _mutation_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _mutation_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _mutation_check(minput, assert_for_error=True)

        # --- member user (error since input is empty)
        self.force_login(self.member_user)
        _mutation_check(minput, okay=False)

        # using private_analysis_pillar for private project validation
        minput['analysisPillar'] = str(private_analysis_pillar.id)

        # --- member user (error since the project is private)
        self.force_login(self.member_user)
        _private_project_mutation_check(minput, okay=False)

        # Valid data
        minput['analysisPillar'] = str(analysis_pillar.id)

        # --- member user (All good)
        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_summary_id = response['data']['project']['triggerAnalysisTopicModel']['result']['id']
        assert _query_check(a_summary_id)['data']['project']['analysisTopicModel']['status'] ==\
            self.genum(TopicModel.Status.STARTED)

        # -- Bad status code from NLP on trigger request
        trigger_results_mock.post.side_effect = nlp_fail_mock

        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_summary_id = response['data']['project']['triggerAnalysisTopicModel']['result']['id']
        assert _query_check(a_summary_id)['data']['project']['analysisTopicModel']['status'] ==\
            self.genum(TopicModel.Status.SEND_FAILED)

        topic_model = TopicModel.objects.get(pk=a_summary_id)
        # Check if generated entries are within the project
        assert list(topic_model.get_entries_qs().values_list('id', flat=True)) == [
            entry.id
            for entry in lead2_entries
        ]

        # -- Callback test (Mocking NLP part)
        SAMPLE_TOPIC_MODEL_RESPONSE = {
            'cluster_1': {
                "entry_id": [
                    entry.id
                    for entry in lead2_entries[:1]
                ],
                'label': "Label 1",
            },
            'cluster_2': {
                "entry_id": [
                    entry.id
                    for entry in lead2_entries[1:]
                ],
                'label': "Label 2"
            }
        }
        RequestHelperMock.return_value.json.return_value = SAMPLE_TOPIC_MODEL_RESPONSE

        callback_url = '/api/v1/callback/analysis-topic-model/'

        data = {
            'client_id': 'invalid-id',
            'presigned_s3_url': 'https://random-domain.com/random-url.json',
            'status': DeeplServerBaseCallbackSerializer.Status.SUCCESS.value,
        }
        response = self.client.post(callback_url, data)
        self.assert_400(response)

        # With valid client_id
        data['client_id'] = AnalysisAutomaticSummaryHandler.get_client_id(topic_model)
        response = self.client.post(callback_url, data)
        self.assert_200(response)

        topic_model.refresh_from_db()
        assert topic_model.status == TopicModel.Status.SUCCESS.value
        assert [
            {
                'entries_id': list(cluster.entries.order_by('id').values_list('id', flat=True))
            }
            for cluster in TopicModelCluster.objects.filter(topic_model=topic_model)
        ] == [
            {'entries_id': [entry.id for entry in lead2_entries[:1]]},
            {'entries_id': [entry.id for entry in lead2_entries[1:]]},
        ]

        # -- Check query data after mock callback
        response_result = _query_check(a_summary_id)['data']['project']['analysisTopicModel']
        assert response_result['status'] == self.genum(TopicModel.Status.SUCCESS)
        assert response_result['clusters'] == [
            {'entries': [dict(id=str(entry.id), excerpt=entry.excerpt) for entry in lead2_entries[:1]]},
            {'entries': [dict(id=str(entry.id), excerpt=entry.excerpt) for entry in lead2_entries[1:]]},
        ]

        # With failed status
        data['status'] = DeeplServerBaseCallbackSerializer.Status.FAILED.value
        response = self.client.post(callback_url, data)
        self.assert_200(response)

        topic_model.refresh_from_db()
        assert topic_model.status == TopicModel.Status.FAILED

    @mock.patch('deepl_integration.handlers.RequestHelper')
    @mock.patch('deepl_integration.handlers.requests')
    def test_automatic_summary(self, trigger_results_mock, RequestHelperMock):
        lead1 = LeadFactory.create(project=self.project)
        lead2 = LeadFactory.create(project=self.project)
        another_lead = LeadFactory.create(project=self.another_project)
        lead3 = LeadFactory.create(project=self.private_project)
        lead1_entries = EntryFactory.create_batch(3, analysis_framework=self.af, lead=lead1)
        lead2_entries = EntryFactory.create_batch(4, analysis_framework=self.af, lead=lead2)
        another_lead_entries = EntryFactory.create_batch(4, analysis_framework=self.af, lead=another_lead)
        lead3_entries = EntryFactory.create_batch(2, analysis_framework=self.af, lead=lead3)

        def nlp_validator_mock(url, data=None, json=None, **kwargs):
            if not json:
                return mock.MagicMock(status_code=500)

            # Get payload from file
            payload = self.get_json_media_file(
                json['entries_url'].split('http://testserver/media/')[1],
            )

            if 'data' in payload and isinstance(payload['data'], list):
                entry_ids = [entry['entry_id'] for entry in payload['data']]

                # NOTE: Confidential leads entries should not be included
                for entry in lead3_entries:
                    if str(entry.id) in entry_ids:
                        assert False, 'Confidential entries should not be included'

            return mock.MagicMock(status_code=202)

        def nlp_fail_mock(*args, **kwargs):
            return mock.MagicMock(status_code=500)

        trigger_results_mock.post.side_effect = nlp_validator_mock

        def _mutation_check(minput, **kwargs):
            return self.query_check(
                self.TRIGGER_AUTOMATIC_SUMMARY,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.project.id},
                **kwargs
            )

        def _private_project_mutation_check(minput, **kwargs):
            return self.query_check(
                self.TRIGGER_AUTOMATIC_SUMMARY,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.private_project.id},
                **kwargs
            )

        def _query_check(_id):
            return self.query_check(
                self.QUERY_AUTOMATIC_SUMMARY,
                minput=minput,
                variables={'projectId': self.project.id, 'summaryID': _id},
            )

        minput = dict(entriesId=[])

        # -- Without login
        _mutation_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _mutation_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _mutation_check(minput, assert_for_error=True)

        # --- member user (error since input is empty)
        self.force_login(self.member_user)
        _mutation_check(minput, okay=False)

        minput['entriesId'] = [
            str(entry.id)
            for entries in [
                lead1_entries,
                lead2_entries,
                another_lead_entries,
                lead3_entries,
            ]
            for entry in entries
        ]
        minput['widgetTags'] = [
            'tag1',
            'tag2',
        ]

        # --- member user (error since the project is private)
        self.force_login(self.member_user)
        response = _private_project_mutation_check(minput, okay=False)

        # --- member user (All good)
        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_summary_id = response['data']['project']['triggerAnalysisAutomaticSummary']['result']['id']
        assert _query_check(a_summary_id)['data']['project']['analysisAutomaticSummary']['status'] ==\
            self.genum(AutomaticSummary.Status.STARTED)

        # Clear out
        AutomaticSummary.objects.get(pk=a_summary_id).delete()

        # -- Bad status code from NLP on trigger request
        trigger_results_mock.post.side_effect = nlp_fail_mock

        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_summary_id = response['data']['project']['triggerAnalysisAutomaticSummary']['result']['id']
        assert _query_check(a_summary_id)['data']['project']['analysisAutomaticSummary']['status'] ==\
            self.genum(AutomaticSummary.Status.SEND_FAILED)

        a_summary = AutomaticSummary.objects.get(pk=a_summary_id)
        # Check if generated entries are within the project
        assert a_summary.entries_id == [
            entry.id
            for entries in [
                lead1_entries,
                lead2_entries,
            ]
            for entry in entries
        ]

        # -- Callback test (Mocking NLP part)
        SAMPLE_SUMMARY_JSON = {
            "summary": "Sample summary text",
            "info_gaps": "Sample Info gaps",
            "analytical_statement": "Sample Analytical Statement"
        }
        RequestHelperMock.return_value.json.return_value = SAMPLE_SUMMARY_JSON

        callback_url = '/api/v1/callback/analysis-automatic-summary/'

        data = {
            'client_id': 'invalid-id',
            'presigned_s3_url': 'https://random-domain.com/random-url.json',
            'status': DeeplServerBaseCallbackSerializer.Status.SUCCESS.value,
        }
        response = self.client.post(callback_url, data)
        self.assert_400(response)

        # With valid client_id
        data['client_id'] = AnalysisAutomaticSummaryHandler.get_client_id(a_summary)
        response = self.client.post(callback_url, data)
        self.assert_200(response)

        a_summary.refresh_from_db()
        assert a_summary.status == AutomaticSummary.Status.SUCCESS.value
        assert a_summary.summary == SAMPLE_SUMMARY_JSON['summary']
        assert a_summary.information_gap == SAMPLE_SUMMARY_JSON['info_gaps']
        assert a_summary.analytical_statement == SAMPLE_SUMMARY_JSON['analytical_statement']

        # -- Check existing instance if provided until threshold is over
        response_result = _mutation_check(minput, okay=True)['data']['project']['triggerAnalysisAutomaticSummary']['result']
        assert response_result['id'] == a_summary_id
        assert response_result['summary'] == SAMPLE_SUMMARY_JSON['summary']
        assert response_result['informationGap'] == SAMPLE_SUMMARY_JSON['info_gaps']
        assert response_result['analyticalStatement'] == SAMPLE_SUMMARY_JSON['analytical_statement']

        a_summary.created_at = self.PATCHER_NOW_VALUE -\
            datetime.timedelta(hours=AutomaticSummary.CACHE_THRESHOLD_HOURS + 1)
        a_summary.save()

        response_result = _mutation_check(minput, okay=True)['data']['project']['triggerAnalysisAutomaticSummary']['result']
        assert response_result['id'] != a_summary_id
        assert response_result['summary'] != SAMPLE_SUMMARY_JSON['summary']

        # With failed status
        data['status'] = DeeplServerBaseCallbackSerializer.Status.FAILED.value
        response = self.client.post(callback_url, data)
        self.assert_200(response)

        a_summary.refresh_from_db()
        assert a_summary.status == AutomaticSummary.Status.FAILED

    @mock.patch('deepl_integration.handlers.RequestHelper')
    @mock.patch('deepl_integration.handlers.requests')
    def test_automatic_ngram(self, trigger_results_mock, RequestHelperMock):
        lead1 = LeadFactory.create(project=self.project)
        lead2 = LeadFactory.create(project=self.project)
        another_lead = LeadFactory.create(project=self.another_project)
        lead1_entries = EntryFactory.create_batch(3, analysis_framework=self.af, lead=lead1)
        lead2_entries = EntryFactory.create_batch(4, analysis_framework=self.af, lead=lead2)
        another_lead_entries = EntryFactory.create_batch(4, analysis_framework=self.af, lead=another_lead)

        trigger_results_mock.post.return_value.status_code = 202

        def _mutation_check(minput, **kwargs):
            return self.query_check(
                self.TRIGGER_AUTOMATIC_NGRAM,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.project.id},
                **kwargs
            )

        def _query_check(_id):
            return self.query_check(
                self.QUERY_AUTOMATIC_NGRAM,
                minput=minput,
                variables={'projectId': self.project.id, 'ngramID': _id},
            )

        minput = dict(entriesId=[])

        # -- Without login
        _mutation_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _mutation_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _mutation_check(minput, assert_for_error=True)

        # --- member user (error since input is empty)
        self.force_login(self.member_user)
        _mutation_check(minput, okay=False)

        minput['entriesId'] = [
            str(entry.id)
            for entries in [
                lead1_entries,
                lead2_entries,
                another_lead_entries
            ]
            for entry in entries
        ]

        # --- member user (All good)
        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_ngram_id = response['data']['project']['triggerAnalysisAutomaticNgram']['result']['id']
        assert _query_check(a_ngram_id)['data']['project']['analysisAutomaticNgram']['status'] ==\
            self.genum(AnalyticalStatementNGram.Status.STARTED)

        # Clear out
        AnalyticalStatementNGram.objects.get(pk=a_ngram_id).delete()

        # -- Bad status code from NLP on trigger request
        trigger_results_mock.post.return_value.status_code = 500

        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_ngram_id = response['data']['project']['triggerAnalysisAutomaticNgram']['result']['id']
        assert _query_check(a_ngram_id)['data']['project']['analysisAutomaticNgram']['status'] ==\
            self.genum(AnalyticalStatementNGram.Status.SEND_FAILED)

        a_ngram = AnalyticalStatementNGram.objects.get(pk=a_ngram_id)
        # Check if generated entries are within the project
        assert a_ngram.entries_id == [
            entry.id
            for entries in [
                lead1_entries,
                lead2_entries,
            ]
            for entry in entries
        ]

        # -- Callback test (Mocking NLP part)
        SAMPLE_NGRAM_RESPONSE = {
            'unigrams': {
                'unigrams-word-1': 1,
                'unigrams-word-2': 1,
                'unigrams-word-5': 3,
            },
            'bigrams': {
                'bigrams-word-2': 1,
                'bigrams-word-3': 0,
                'bigrams-word-4': 2,
            },
        }
        RequestHelperMock.return_value.json.return_value = SAMPLE_NGRAM_RESPONSE

        callback_url = '/api/v1/callback/analysis-automatic-ngram/'

        data = {
            'client_id': 'invalid-id',
            'presigned_s3_url': 'https://random-domain.com/random-url.json',
            'status': DeeplServerBaseCallbackSerializer.Status.SUCCESS.value,
        }
        response = self.client.post(callback_url, data)
        self.assert_400(response)

        # With valid client_id
        data['client_id'] = AnalysisAutomaticSummaryHandler.get_client_id(a_ngram)
        response = self.client.post(callback_url, data)
        self.assert_200(response)

        a_ngram.refresh_from_db()
        assert a_ngram.status == AnalyticalStatementNGram.Status.SUCCESS.value
        assert a_ngram.unigrams == SAMPLE_NGRAM_RESPONSE['unigrams']
        assert a_ngram.bigrams == SAMPLE_NGRAM_RESPONSE['bigrams']
        assert a_ngram.trigrams == {}

        # -- Check existing instance if provided until threshold is over
        response_result = _mutation_check(minput, okay=True)['data']['project']['triggerAnalysisAutomaticNgram']['result']
        assert response_result['id'] == a_ngram_id
        assert response_result['unigrams'] == [
            dict(word=word, count=count)
            for word, count in SAMPLE_NGRAM_RESPONSE['unigrams'].items()
        ]
        assert response_result['bigrams'] == [
            dict(word=word, count=count)
            for word, count in SAMPLE_NGRAM_RESPONSE['bigrams'].items()
        ]
        assert response_result['trigrams'] == []

        a_ngram.created_at = self.PATCHER_NOW_VALUE -\
            datetime.timedelta(hours=AnalyticalStatementNGram.CACHE_THRESHOLD_HOURS + 1)
        a_ngram.save()

        response_result = _mutation_check(minput, okay=True)['data']['project']['triggerAnalysisAutomaticNgram']['result']
        assert response_result['id'] != a_ngram_id
        assert response_result['unigrams'] == []
        assert response_result['bigrams'] == []
        assert response_result['trigrams'] == []

        # With failed status
        data['status'] = DeeplServerBaseCallbackSerializer.Status.FAILED.value
        response = self.client.post(callback_url, data)
        self.assert_200(response)

        a_ngram.refresh_from_db()
        assert a_ngram.status == AnalyticalStatementNGram.Status.FAILED

    @mock.patch('deepl_integration.handlers.RequestHelper')
    @mock.patch('deepl_integration.handlers.requests')
    def test_geo_location(self, trigger_results_mock, RequestHelperMock):
        lead1 = LeadFactory.create(project=self.project)
        lead2 = LeadFactory.create(project=self.project)
        another_lead = LeadFactory.create(project=self.another_project)
        lead1_entries = EntryFactory.create_batch(3, analysis_framework=self.af, lead=lead1)
        lead2_entries = EntryFactory.create_batch(4, analysis_framework=self.af, lead=lead2)
        another_lead_entries = EntryFactory.create_batch(4, analysis_framework=self.af, lead=another_lead)

        trigger_results_mock.post.return_value.status_code = 202

        def _mutation_check(minput, **kwargs):
            return self.query_check(
                self.TRIGGER_GEOLOCATION,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.project.id},
                **kwargs
            )

        def _query_check(_id):
            return self.query_check(
                self.QUERY_GEOLOCATION,
                minput=minput,
                variables={'projectId': self.project.id, 'ID': _id},
            )

        minput = dict(entriesId=[])

        # -- Without login
        _mutation_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _mutation_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _mutation_check(minput, assert_for_error=True)

        # --- member user (error since input is empty)
        self.force_login(self.member_user)
        _mutation_check(minput, okay=False)

        minput['entriesId'] = [
            str(entry.id)
            for entries in [
                lead1_entries,
                lead2_entries,
                another_lead_entries
            ]
            for entry in entries
        ]

        # --- member user (All good)
        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            geo_task_id = response['data']['project']['triggerAnalysisGeoLocation']['result']['id']
        assert _query_check(geo_task_id)['data']['project']['analysisGeoTask']['status'] ==\
            self.genum(AnalyticalStatementGeoTask.Status.STARTED)

        # Clear out
        AnalyticalStatementGeoTask.objects.get(pk=geo_task_id).delete()

        # -- Bad status code from NLP on trigger request
        trigger_results_mock.post.return_value.status_code = 500

        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            geo_task_id = response['data']['project']['triggerAnalysisGeoLocation']['result']['id']
        assert _query_check(geo_task_id)['data']['project']['analysisGeoTask']['status'] ==\
            self.genum(AnalyticalStatementGeoTask.Status.SEND_FAILED)

        geo_task = AnalyticalStatementGeoTask.objects.get(pk=geo_task_id)
        # Check if generated entries are within the project
        assert geo_task.entries_id == [
            entry.id
            for entries in [
                lead1_entries,
                lead2_entries,
            ]
            for entry in entries
        ]

        # -- Callback test (Mocking NLP part)
        CALLBACK_ENTRIES = lead1_entries
        SAMPLE_GEO_DATA_RESPONSE = [
            {
                'entry_id': str(entry.id),
                'locations': [
                    {
                        'entity': 'test',
                        'meta':
                            {
                                'latitude': 11,
                                'longitude': 11,
                                'offset_start': 0,
                                'offset_end': 3,
                            }

                    }
                ]
            }
            for entry in [
                *CALLBACK_ENTRIES,
                *another_lead_entries,  # Invalid entries
            ]
        ]

        RequestHelperMock.return_value.json.return_value = SAMPLE_GEO_DATA_RESPONSE

        callback_url = '/api/v1/callback/analysis-geo/'

        data = {
            'client_id': 'invalid-id',
            'presigned_s3_url': 'https://random-domain.com/random-url.json',
            'status': DeeplServerBaseCallbackSerializer.Status.SUCCESS.value,
        }
        response = self.client.post(callback_url, data)
        self.assert_400(response)

        # With valid client_id
        data['client_id'] = AnalysisAutomaticSummaryHandler.get_client_id(geo_task)
        response = self.client.post(callback_url, data)
        self.assert_200(response)

        geo_task.refresh_from_db()
        assert geo_task.status == AnalyticalStatementGeoTask.Status.SUCCESS.value
        assert _query_check(geo_task.id)['data']['project']['analysisGeoTask']['entryGeo'] == [
            {
                'data':
                [
                    {
                        'entity': 'test',
                        'meta':
                            {
                                'latitude': 11,
                                'longitude': 11,
                                'offsetStart': 0,
                                'offsetEnd': 3,
                            },
                    },
                ],
                'entryId': str(entry.id),
            }
            for entry in CALLBACK_ENTRIES
        ]

        # -- Check existing instance if provided until threshold is over (CACHE check)
        response_result = _mutation_check(minput, okay=True)['data']['project']['triggerAnalysisGeoLocation']['result']
        assert response_result['id'] == geo_task_id

        geo_task.created_at = self.PATCHER_NOW_VALUE -\
            datetime.timedelta(hours=AnalyticalStatementGeoTask.CACHE_THRESHOLD_HOURS + 1)
        geo_task.save()

        response_result = _mutation_check(minput, okay=True)['data']['project']['triggerAnalysisGeoLocation']['result']
        assert response_result['id'] != geo_task_id

        # With failed status
        data['status'] = DeeplServerBaseCallbackSerializer.Status.FAILED.value
        response = self.client.post(callback_url, data)
        self.assert_200(response)

        geo_task.refresh_from_db()
        assert geo_task.status == AnalyticalStatementGeoTask.Status.FAILED


class TestAnalysisReportQueryAndMutationSchema(GraphQLTestCase):
    factories_used = [
        AnalysisReportUploadFactory,
    ]

    REPORT_SNAPSHOT_FRAGMENT = '''
        fragment AnalysisReportSnapshotResponse on AnalysisReportSnapshotType {
            id
            publishedOn
            report
            publishedBy {
                displayName
            }
            reportDataFile {
              name
              url
            }
            files {
              id
              title
              mimeType
              metadata
              file {
                name
                url
              }
            }
        }
    '''

    CREATE_REPORT = (
        SnapshotQuery.AnalysisReport.SnapshotFragment +
        '''\n
        mutation CreateReport($projectId: ID!, $input: AnalysisReportInputType!) {
          project(id: $projectId) {
            analysisReportCreate(data: $input) {
              result {
                ...AnalysisReportQueryType
              }
              errors
              ok
            }
          }
        }
        '''
    )

    CREATE_REPORT_SNAPSHOT = (
        REPORT_SNAPSHOT_FRAGMENT +
        '''\n
        mutation CreateReportSnapshot($projectId: ID!, $input: AnalysisReportSnapshotInputType!) {
          project(id: $projectId) {
            analysisReportSnapshotCreate(data: $input) {
              result {
                 ...AnalysisReportSnapshotResponse
              }
              errors
              ok
            }
          }
        }
        '''
    )

    UPDATE_REPORT = (
        SnapshotQuery.AnalysisReport.SnapshotFragment +
        '''\n
        mutation UpdateReport($projectId: ID!, $reportId: ID!, $input: AnalysisReportInputUpdateType!) {
          project(id: $projectId) {
            analysisReportUpdate(id: $reportId, data: $input) {
              result {
                ...AnalysisReportQueryType
              }
              errors
              ok
            }
          }
        }
        '''
    )

    QUERY_REPORT = (
        SnapshotQuery.AnalysisReport.SnapshotFragment +
        '''\n
        query Report($projectId: ID!, $reportId: ID!) {
          project(id: $projectId) {
            analysisReport(id: $reportId) {
              ...AnalysisReportQueryType
            }
          }
        }
        '''
    )

    QUERY_REPORT_SNAPSHOT = (
        REPORT_SNAPSHOT_FRAGMENT +
        '''\n
        query QueryReportSnapshot($projectId: ID!, $snapshotId: ID!) {
          project(id: $projectId) {
            analysisReportSnapshot(id: $snapshotId) {
              ...AnalysisReportSnapshotResponse
            }
          }
        }
        '''
    )

    QUERY_PUBLIC_REPORT_SNAPSHOT = (
        REPORT_SNAPSHOT_FRAGMENT +
        '''\n
        query QueryPublicReportSnapshot($slug: String!) {
          publicAnalysisReportSnapshot(slug: $slug) {
            ...AnalysisReportSnapshotResponse
          }
        }
        '''
    )

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        # User with role
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.member_user = UserFactory.create()
        self.project.add_member(self.member_user, role=self.project_role_member)
        self.project.add_member(self.readonly_member_user, role=self.project_role_reader)

    def test_mutation_and_query(self):
        analysis = AnalysisFactory.create(
            project=self.project,
            team_lead=self.member_user,
            end_date=datetime.date(2022, 4, 1),
        )

        def _create_mutation_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_REPORT,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.project.id},
                **kwargs
            )

        def _create_snapshot_mutation_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_REPORT_SNAPSHOT,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.project.id},
                **kwargs
            )

        def _query_snapshot_check(snapshot_id, **kwargs):
            return self.query_check(
                self.QUERY_REPORT_SNAPSHOT,
                variables={
                    'projectId': self.project.id,
                    'snapshotId': snapshot_id
                },
                **kwargs,
            )

        def _query_public_snapshot_check(slug, **kwargs):
            return self.query_check(
                self.QUERY_PUBLIC_REPORT_SNAPSHOT,
                variables={
                    'slug': slug
                },
                **kwargs,
            )

        def _update_mutation_check(_id, minput, **kwargs):
            return self.query_check(
                self.UPDATE_REPORT,
                minput=minput,
                mnested=['project'],
                variables={
                    'projectId': self.project.id,
                    'reportId': _id,
                },
                **kwargs
            )

        def _query_check(_id, **kwargs):
            return self.query_check(
                self.QUERY_REPORT,
                variables={
                    'projectId': self.project.id,
                    'reportId': _id
                },
                **kwargs,
            )

        test_data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'analysis_report',
        )
        with\
                open(os.path.join(test_data_dir, 'data.json'), 'r') as test_data_file, \
                open(os.path.join(test_data_dir, 'error1.json'), 'r') as test_error1_file, \
                open(os.path.join(test_data_dir, 'error2.json'), 'r') as test_error2_file:
            test_data = json.load(test_data_file)
            error_1_data = json.load(test_error1_file)
            error_2_data = json.load(test_error2_file)

        minput = {
            'isPublic': False,
            'analysis': str(analysis.pk),
            'slug': 'analysis-test-1001',
            'title': 'Test 2',
            'subTitle': 'Test 2',
            **test_data,
        }

        # Create
        # -- Without login
        _create_mutation_check(minput, assert_for_error=True)
        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _create_mutation_check(minput, assert_for_error=True)
        _create_mutation_check(minput, assert_for_error=True)
        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _create_mutation_check(minput, assert_for_error=True)

        # --- member user (All good)
        self.force_login(self.member_user)
        response = _create_mutation_check(minput, okay=True)
        created_report1_data = response['data']['project']['analysisReportCreate']['result']
        report1_id = created_report1_data['id']

        report1_upload1, report1_upload2 = AnalysisReportUploadFactory.create_batch(2, report_id=report1_id)

        minput['containers'][0]['contentData'] = [{
            'clientReferenceId': 'upload-1-id',
            'upload': str(report1_upload1.pk),
        }]

        # -- Validation check
        errors = _create_mutation_check(
            minput,
            okay=False,
        )['data']['project']['analysisReportCreate']['errors']
        assert errors == error_1_data
        del errors

        minput['containers'][0]['contentData'] = []
        minput['slug'] = 'analysis-test-1002'
        created_report2_data = _create_mutation_check(
            minput,
            okay=True,
        )['data']['project']['analysisReportCreate']['result']
        report2_id = created_report2_data['id']

        # Update
        # -- -- Report 1
        minput = {
            **created_report1_data,
        }
        minput.pop('id')
        # -- Without login
        self.logout()
        _update_mutation_check(report1_id, minput, assert_for_error=True)
        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _update_mutation_check(report1_id, minput, assert_for_error=True)
        _update_mutation_check(report1_id, minput, assert_for_error=True)
        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _update_mutation_check(report1_id, minput, assert_for_error=True)

        # --- member user (error since input is empty)
        self.force_login(self.member_user)
        response = _update_mutation_check(report1_id, minput, okay=True)
        updated_report_data = response['data']['project']['analysisReportUpdate']['result']
        assert updated_report_data == created_report1_data
        del updated_report_data
        # -- -- Report 2
        minput = {
            **created_report2_data,
        }
        minput.pop('id')
        # Invalid data
        minput['containers'][0]['contentData'] = [{
            'clientReferenceId': 'upload-2-id',
            'upload': str(report1_upload2.pk),
        }]
        errors = _update_mutation_check(
            report2_id,
            minput,
            okay=False,
        )['data']['project']['analysisReportUpdate']['errors']

        assert errors == error_2_data

        report2_upload1 = AnalysisReportUploadFactory.create(report_id=report2_id)
        minput['containers'][0]['contentData'] = [{
            'clientReferenceId': 'upload-1-id',
            'upload': str(report2_upload1.pk),
        }]
        response = _update_mutation_check(report2_id, minput, okay=True)
        updated_report_data = response['data']['project']['analysisReportUpdate']['result']
        assert updated_report_data != created_report2_data

        # Basic query check
        # -- Without login
        self.logout()
        _query_check(report1_id, assert_for_error=True)
        _query_check(report2_id, assert_for_error=True)
        # -- With login (non-member)
        self.force_login(self.non_member_user)
        assert _query_check(report1_id)['data']['project']['analysisReport'] is None
        assert _query_check(report2_id)['data']['project']['analysisReport'] is None
        # --- member user
        for user in [
            self.readonly_member_user,
            self.member_user
        ]:
            self.force_login(user)
            assert _query_check(report1_id)['data']['project']['analysisReport'] is not None
            assert _query_check(report2_id)['data']['project']['analysisReport'] is not None

        # Snapshot Mutation
        minput = {'report': str(report1_id)}
        self.logout()
        _create_snapshot_mutation_check(minput, assert_for_error=True)
        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _create_snapshot_mutation_check(minput, assert_for_error=True)
        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _create_snapshot_mutation_check(minput, assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)
        snapshot_data = _create_snapshot_mutation_check(
            minput,
            okay=True,
        )['data']['project']['analysisReportSnapshotCreate']['result']
        snapshot_id = snapshot_data['id']
        assert snapshot_data['report'] == minput['report']
        assert snapshot_data['reportDataFile']['url'] not in ['', None]

        another_report = AnalysisReportFactory.create(
            analysis=AnalysisFactory.create(
                project=ProjectFactory.create(),
                team_lead=self.member_user,
                end_date=datetime.date(2022, 4, 1),
            )
        )
        minput = {'report': str(another_report.pk)}
        _create_snapshot_mutation_check(minput, okay=False)

        # Snapshot Query
        self.logout()
        _query_snapshot_check(snapshot_id, assert_for_error=True)
        # -- With login (non-member)
        self.force_login(self.non_member_user)
        assert _query_snapshot_check(
            snapshot_id,
        )['data']['project']['analysisReportSnapshot'] is None
        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        assert _query_snapshot_check(
            snapshot_id,
        )['data']['project']['analysisReportSnapshot'] is not None
        # --- member user
        self.force_login(self.member_user)
        assert _query_snapshot_check(
            snapshot_id,
        )['data']['project']['analysisReportSnapshot'] is not None

        # Snapshot Public Query
        snapshot = AnalysisReportSnapshot.objects.get(pk=snapshot_id)
        snapshot_slug = snapshot.report.slug

        # -- Not Public [Not enabled in project]
        snapshot.report.is_public = False
        snapshot.report.save()
        for user in [
            None,
            self.non_member_user,
            self.readonly_member_user,
            self.member_user,
        ]:
            if user is None:
                self.logout()
            else:
                self.force_login(user)
            assert _query_public_snapshot_check(snapshot_slug)['data']['publicAnalysisReportSnapshot'] is None

        # -- Public [Not enabled in project]
        snapshot.report.is_public = True
        snapshot.report.save()
        for user in [
            None,
            self.non_member_user,
            self.readonly_member_user,
            self.member_user,
        ]:
            if user is None:
                self.logout()
            else:
                self.force_login(user)
            assert _query_public_snapshot_check(snapshot_slug)['data']['publicAnalysisReportSnapshot'] is None

        self.project.enable_publicly_viewable_analysis_report_snapshot = True
        self.project.save(update_fields=('enable_publicly_viewable_analysis_report_snapshot',))
        # -- Not Public [Enabled in project]
        snapshot.report.is_public = False
        snapshot.report.save()
        for user in [
            None,
            self.non_member_user,
            self.readonly_member_user,
            self.member_user,
        ]:
            if user is None:
                self.logout()
            else:
                self.force_login(user)
            assert _query_public_snapshot_check(snapshot_slug)['data']['publicAnalysisReportSnapshot'] is None

        # -- Public [Enabled in project]
        snapshot.report.is_public = True
        snapshot.report.save()
        for user in [
            None,
            self.non_member_user,
            self.readonly_member_user,
            self.member_user,
        ]:
            if user is None:
                self.logout()
            else:
                self.force_login(user)
            assert _query_public_snapshot_check(snapshot_slug)['data']['publicAnalysisReportSnapshot'] is not None
