import datetime
from unittest import mock
from utils.graphene.tests import GraphQLTestCase

from deepl_integration.handlers import AnalysisAutomaticSummaryHandler
from deepl_integration.serializers import DeeplServerBaseCallbackSerializer

from user.factories import UserFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from analysis.factories import AnalysisFactory, AnalysisPillarFactory

from analysis.models import (
    TopicModel,
    TopicModelCluster,
    AutomaticSummary,
    AnalyticalStatementNGram,
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
            triggerTopicModel(data: $input) {
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
            triggerAutomaticSummary(data: $input) {
              ok
              errors
              result {
                id
                status
                summary
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
            triggerAutomaticNgram(data: $input) {
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

    def setUp(self):
        super().setUp()
        self.af = AnalysisFrameworkFactory.create()
        self.project = ProjectFactory.create(analysis_framework=self.af)
        self.another_project = ProjectFactory.create()
        # User with role
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.member_user = UserFactory.create()
        self.project.add_member(self.member_user, role=self.project_role_member)

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

        trigger_results_mock.post.return_value.status_code = 202

        def _mutation_check(minput, **kwargs):
            return self.query_check(
                self.TRIGGER_TOPIC_MODEL,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.project.id},
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

        # Valid data
        minput['analysisPillar'] = str(analysis_pillar.id)

        # --- member user (All good)
        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_summary_id = response['data']['project']['triggerTopicModel']['result']['id']
        assert _query_check(a_summary_id)['data']['project']['analysisTopicModel']['status'] ==\
            self.genum(TopicModel.Status.STARTED)

        # -- Bad status code from NLP on trigger request
        trigger_results_mock.post.return_value.status_code = 500

        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_summary_id = response['data']['project']['triggerTopicModel']['result']['id']
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
            'cluster_1': [
                entry.id
                for entry in lead2_entries[:1]
            ],
            'cluster_2': [
                entry.id
                for entry in lead2_entries[1:]
            ]
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
        lead1_entries = EntryFactory.create_batch(3, analysis_framework=self.af, lead=lead1)
        lead2_entries = EntryFactory.create_batch(4, analysis_framework=self.af, lead=lead2)
        another_lead_entries = EntryFactory.create_batch(4, analysis_framework=self.af, lead=another_lead)

        trigger_results_mock.post.return_value.status_code = 202

        def _mutation_check(minput, **kwargs):
            return self.query_check(
                self.TRIGGER_AUTOMATIC_SUMMARY,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.project.id},
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
                another_lead_entries
            ]
            for entry in entries
        ]

        # --- member user (All good)
        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_summary_id = response['data']['project']['triggerAutomaticSummary']['result']['id']
        assert _query_check(a_summary_id)['data']['project']['analysisAutomaticSummary']['status'] ==\
            self.genum(AutomaticSummary.Status.STARTED)

        # Clear out
        AutomaticSummary.objects.get(pk=a_summary_id).delete()

        # -- Bad status code from NLP on trigger request
        trigger_results_mock.post.return_value.status_code = 500

        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_summary_id = response['data']['project']['triggerAutomaticSummary']['result']['id']
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
        SAMPLE_SUMMARY_TEXT = 'SAMPLE SUMMARY TEXT'
        RequestHelperMock.return_value.get_text.return_value = SAMPLE_SUMMARY_TEXT

        callback_url = '/api/v1/callback/analysis-automatic-summary/'

        data = {
            'client_id': 'invalid-id',
            'presigned_s3_url': 'https://random-domain.com/random-url.txt',
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
        assert a_summary.summary == SAMPLE_SUMMARY_TEXT

        # -- Check existing instance if provided until threshold is over
        response_result = _mutation_check(minput, okay=True)['data']['project']['triggerAutomaticSummary']['result']
        assert response_result['id'] == a_summary_id
        assert response_result['summary'] == SAMPLE_SUMMARY_TEXT

        a_summary.created_at = self.PATCHER_NOW_VALUE -\
            datetime.timedelta(hours=AutomaticSummary.CACHE_THRESHOLD_HOURS + 1)
        a_summary.save()

        response_result = _mutation_check(minput, okay=True)['data']['project']['triggerAutomaticSummary']['result']
        assert response_result['id'] != a_summary_id
        assert response_result['summary'] != SAMPLE_SUMMARY_TEXT

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
            a_ngram_id = response['data']['project']['triggerAutomaticNgram']['result']['id']
        assert _query_check(a_ngram_id)['data']['project']['analysisAutomaticNgram']['status'] ==\
            self.genum(AnalyticalStatementNGram.Status.STARTED)

        # Clear out
        AnalyticalStatementNGram.objects.get(pk=a_ngram_id).delete()

        # -- Bad status code from NLP on trigger request
        trigger_results_mock.post.return_value.status_code = 500

        with self.captureOnCommitCallbacks(execute=True):
            response = _mutation_check(minput, okay=True)
            a_ngram_id = response['data']['project']['triggerAutomaticNgram']['result']['id']
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
        response_result = _mutation_check(minput, okay=True)['data']['project']['triggerAutomaticNgram']['result']
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

        response_result = _mutation_check(minput, okay=True)['data']['project']['triggerAutomaticNgram']['result']
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
