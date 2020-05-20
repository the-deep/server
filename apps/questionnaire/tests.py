from deep.tests import TestCase
from analysis_framework.models import AnalysisFramework
from questionnaire.models import (
    QuestionBase,
    Questionnaire,
    Question,
    FrameworkQuestion,
    CrisisType,
)


# TODO: This tests will fail with --reuse-db. Make sure HStoreExtension is loaded for --reuse-db
# This might be helpfull https://pytest-django.readthedocs.io/en/latest/configuring_django.html
class QuestionnaireTests(TestCase):
    def test_questionnaire_get_api(self):
        project = self.create_project()
        self.create(Questionnaire, project=project, data_collection_techniques=[QuestionBase.DIRECT])
        self.create(Questionnaire, project=project, data_collection_techniques=[QuestionBase.FOCUS_GROUP])
        self.create(Questionnaire, project=project)

        self.authenticate()
        response = self.client.get(f'/api/v1/questionnaires/?project={project.pk}')
        self.assert_200(response)
        assert len(response.json()['results']) == 3

        # Custom filter test
        response = self.client.get(
            f"/api/v1/questionnaires/?project={project.pk}"
            f"&data_collection_techniques={','.join([QuestionBase.DIRECT, QuestionBase.FOCUS_GROUP])}"
        )
        self.assert_200(response)
        assert len(response.json()['results']) == 2

    def test_questionnaire_post_api(self):
        project = self.create_project()
        title = 'Test Questionnaire'

        self.authenticate()
        response = self.client.post('/api/v1/questionnaires/', data={
            'title': title,
            'project': project.pk,
        })
        self.assert_201(response)
        created_questionnaire = Questionnaire.objects.get(pk=response.json()['id'])
        assert created_questionnaire.title == title
        assert created_questionnaire.project == project

    def test_questionnaire_options_api(self):
        self.create(CrisisType, title='Crisis 1')
        self.create(CrisisType, title='Crisis 2')
        self.create(CrisisType, title='Crisis 3')

        self.authenticate()
        response = self.client.get('/api/v1/questionnaires/options/')
        self.assert_200(response)
        assert len(response.json()['crisisTypeOptions']) == 3

    def test_questionnaire_clone_api(self):
        questionnaire = self.create(Questionnaire, title='Test Questionnaire', project=self.create_project())
        self.create(Question, questionnaire=questionnaire)
        self.create(Question, questionnaire=questionnaire)
        self.create(Question, questionnaire=questionnaire)

        self.authenticate()
        response = self.client.post(f'/api/v1/questionnaires/{questionnaire.pk}/clone/')
        self.assert_200(response)
        cloned_questionnaire = Questionnaire.objects.get(pk=response.json()['id'])

        assert cloned_questionnaire.title == questionnaire.title
        assert cloned_questionnaire.question_set.count() == questionnaire.question_set.count()

    def test_question_api(self):
        questionnaire = self.create(Questionnaire, project=self.create_project())
        self.create(Question, questionnaire=questionnaire)
        self.create(Question, questionnaire=questionnaire)
        self.create(Question, questionnaire=questionnaire)

        self.authenticate()
        response = self.client.get(f'/api/v1/questionnaires/{questionnaire.pk}/questions/')
        self.assert_200(response)
        assert len(response.json()['results']) == 3

    def test_question_post_api(self):
        questionnaire = self.create(Questionnaire, project=self.create_project())
        title = 'Test Question'
        more_titles = {
            'en': title,
            'np': 'Test Question in Nepali',
        }

        self.authenticate()
        response = self.client.post(f'/api/v1/questionnaires/{questionnaire.pk}/questions/', data={
            'title': title,
            'name': 'question-1',
            'more_titles': more_titles,
        })
        self.assert_201(response)
        new_question = Question.objects.get(pk=response.json()['id'])
        assert new_question.title == title
        assert new_question.more_titles == more_titles

        response = self.client.post(f'/api/v1/questionnaires/{questionnaire.pk}/questions/', data={
            'title': title,
            'name': 'question-1',
            'more_titles': more_titles,
        })
        # Duplicate name
        self.assert_400(response)

    def test_question_clone_api(self):
        question = self.create(
            Question, title='Test Question',
            questionnaire=self.create(Questionnaire, project=self.create_project())
        )

        self.authenticate()
        response = self.client.post(
            f'/api/v1/questionnaires/{question.questionnaire.pk}/questions/{question.pk}/clone/')
        self.assert_200(response)
        cloned_question = Question.objects.get(pk=response.json()['id'])

        assert cloned_question.title == question.title

    def test_question_bulk_actions_api(self):
        questionnaire = self.create(Questionnaire, project=self.create_project())
        q1 = self.create(Question, title='Test Question', questionnaire=questionnaire)
        q2 = self.create(Question, title='Test Question', questionnaire=questionnaire)
        q3 = self.create(Question, title='Test Question', questionnaire=questionnaire)
        q4 = self.create(Question, title='Test Question', questionnaire=questionnaire)

        def get_bulk_data(questions):
            return [{'id': q.pk} for q in questions]

        self.authenticate()
        # TODO: Detail test
        for action, data, state, excepted_state in [
                (
                    'bulk-archive', get_bulk_data([q1, q2, q3]),
                    lambda: Question.objects.filter(questionnaire=questionnaire, is_archived=True).count(), 3
                ),
                (
                    'bulk-unarchive', get_bulk_data([q1, q2, q3, q4]),
                    lambda: Question.objects.filter(questionnaire=questionnaire, is_archived=False).count(), 4
                ),
                (
                    'bulk-delete', get_bulk_data([q1, q2]),
                    lambda: Question.objects.filter(questionnaire=questionnaire).count(), 2
                ),
        ]:
            response = self.client.post(f'/api/v1/questionnaires/{questionnaire.pk}/questions/{action}/', data=data)
            self.assert_200(response)
            assert state() == excepted_state, f'For {action} {response.json()}'

    def test_question_order_api(self):
        questionnaire = self.create(Questionnaire, project=self.create_project())
        q1 = self.create(Question, title='Test Question', questionnaire=questionnaire, order=1)
        q2 = self.create(Question, title='Test Question', questionnaire=questionnaire, order=2)
        q3 = self.create(Question, title='Test Question', questionnaire=questionnaire, order=3)
        q4 = self.create(Question, title='Test Question', questionnaire=questionnaire, order=4)
        questions = [q1, q2, q3, q4]

        self.authenticate()
        response = self.client.post(
            f'/api/v1/questionnaires/{questionnaire.pk}/questions/{q3.pk}/order/',
            data={'action': 'below', 'value': q1.pk}
        )
        self.assert_200(response)

        # Check new generated orders
        [q.refresh_from_db() for q in questions]
        assert [q.order for q in questions] == [1, 3, 2, 4]

    def test_framework_question_api(self):
        af = self.create(AnalysisFramework)
        self.create(FrameworkQuestion, analysis_framework=af)
        self.create(FrameworkQuestion, analysis_framework=af)
        self.create(FrameworkQuestion, analysis_framework=af)

        self.authenticate()
        response = self.client.get(f'/api/v1/analysis-frameworks/{af.pk}/questions/')
        self.assert_200(response)

    def test_framework_question_post_api(self):
        af = self.create(AnalysisFramework)
        af.add_member(self.user, af.get_or_create_owner_role())
        q1 = self.create(FrameworkQuestion, analysis_framework=af)

        self.authenticate()
        response = self.client.post(f'/api/v1/analysis-frameworks/{af.pk}/questions/', data={
            'title': 'Test Framework Questions',
            'name': 'framework-question-1',
        })
        self.assert_201(response)
        q2_id = response.json()['id']

        response = self.client.post(f'/api/v1/analysis-frameworks/{af.pk}/questions/{q2_id}/order/', data={
            'action': 'above', 'value': q1.pk,
        })
        self.assert_200(response)

    def test_framework_question_copy_api(self):
        af = self.create(AnalysisFramework)
        fq = self.create(FrameworkQuestion, analysis_framework=af)
        questionnaire = self.create(Questionnaire, project=self.create_project())
        self.create(Question, questionnaire=questionnaire)

        self.authenticate()
        response = self.client.post(f'/api/v1/questionnaires/{questionnaire.pk}/questions/af-question-copy/', data={
            'framework_question_id': fq.pk,
            'order_action': {
                'action': 'bottom',
            },
        })
        self.assert_200(response)
        assert response.json()['questionnaire'] == questionnaire.pk
        assert response.json()['order'] == 2

    def test_xform_view(self):
        # Just checking API Endpoint. Requires xform file for test
        self.authenticate()
        response = self.client.post('/api/v1/xlsform-to-xform/')
        self.assert_400(response)

    def test_kobo_toolbox_export(self):
        # Just checking API Endpoint. Requires oauth for test
        self.authenticate()
        response = self.client.post('/api/v1/import-to-kobotoolbox/')
        self.assert_400(response)
