from utils.graphene.tests import GraphQLTestCase

from assisted_tagging.models import (
    AssistedTaggingPrediction,
)

from assisted_tagging.models import (
    AssistedTaggingModelVersion,
    DraftEntry,
)

from lead.factories import LeadFactory
from user.factories import UserFactory
from project.factories import ProjectFactory
from geo.factories import RegionFactory, AdminLevelFactory, GeoAreaFactory

from assisted_tagging.factories import (
    AssistedTaggingModelFactory,
    AssistedTaggingModelPredictionTagFactory,
    AssistedTaggingModelVersionFactory,
    DraftEntryFactory,
    AssistedTaggingPredictionFactory,
)


class TestAssistedTaggingQuery(GraphQLTestCase):
    ENABLE_NOW_PATCHER = True

    ASSISTED_TAGGING_NLP_DATA = '''
        query MyQuery ($taggingModelId: ID! ) {
          assistedTagging {
            taggingModels {
              id
              modelId
              name
              versions {
                id
                version
              }
            }
            taggingModel(id: $taggingModelId) {
              id
              modelId
              name
              versions {
                id
                version
              }
            }
          }
        }
    '''

    ASSISTED_TAGGING_DRAFT_ENTRY = '''
        query MyQuery ($projectId: ID!, $draftEntryId: ID!) {
          project(id: $projectId) {
            assistedTagging {
              draftEntry(id: $draftEntryId) {
                id
                excerpt
                predictionStatus
                predictionStatusDisplay
                predictionReceivedAt
                geoAreas {
                    title
                }
              }
            }
          }
        }
    '''

    def test_unified_connector_nlp_data(self):
        user = UserFactory.create()

        model1, *other_models = AssistedTaggingModelFactory.create_batch(2)
        AssistedTaggingModelVersionFactory.create_batch(2, model=model1)

        # -- without login
        content = self.query_check(
            self.ASSISTED_TAGGING_NLP_DATA,
            variables=dict(
                taggingModelId=model1.id,
            ),
            assert_for_error=True,
        )

        # -- with login
        self.force_login(user)
        content = self.query_check(
            self.ASSISTED_TAGGING_NLP_DATA,
            variables=dict(
                taggingModelId=model1.id,
            )
        )['data']['assistedTagging']
        self.assertEqual(content['taggingModels'], [
            dict(
                id=str(_model.id),
                modelId=_model.model_id,
                name=_model.name,
                versions=[
                    dict(
                        id=str(model_version.id),
                        version=str(model_version.version),
                    )
                    for model_version in _model.versions.order_by('-version').all()
                ],
            )
            for _model in [model1, *other_models]
        ])
        self.assertEqual(content['taggingModel'], dict(
            id=str(model1.id),
            modelId=model1.model_id,
            name=model1.name,
            versions=[
                dict(
                    id=str(model_version.id),
                    version=str(model_version.version),
                )
                for model_version in model1.versions.all()
            ],
        ))

    def test_unified_connector_draft_entry(self):
        project = ProjectFactory.create()
        region = RegionFactory.create(is_published=True)
        admin_level = AdminLevelFactory.create(region=region)
        lead = LeadFactory.create(project=project)
        user = UserFactory.create()
        another_user = UserFactory.create()
        project.add_member(user)
        project.regions.add(region)
        self.maxDiff = None

        GeoAreaFactory.create(admin_level=admin_level, title='Nepal')
        GeoAreaFactory.create(admin_level=admin_level, title='Bagmati')
        GeoAreaFactory.create(admin_level=admin_level, title='Kathmandu')
        draft_entry1 = DraftEntryFactory.create(project=project, lead=lead, excerpt='sample excerpt')

        draft_entry1.save_geo_data()

        def _query_check(**kwargs):
            return self.query_check(
                self.ASSISTED_TAGGING_DRAFT_ENTRY,
                variables=dict(
                    projectId=project.id,
                    draftEntryId=draft_entry1.id,
                ),
                **kwargs,
            )

        # -- without login
        _query_check(assert_for_error=True)

        # -- with login (non-member)
        self.force_login(another_user)
        content = _query_check()
        self.assertIsNone(content['data']['project']['assistedTagging'])

        # -- with login (member)
        self.force_login(user)
        content = _query_check()['data']['project']['assistedTagging']['draftEntry']
        self.assertEqual(content, dict(
            id=str(draft_entry1.pk),
            excerpt=draft_entry1.excerpt,
            predictionReceivedAt=None,
            predictionStatus=self.genum(draft_entry1.prediction_status),
            predictionStatusDisplay=draft_entry1.get_prediction_status_display(),
            geoAreas=[]
        ))


class TestAssistedTaggingModules(GraphQLTestCase):

    def test_assisted_tagging_model_version_latest_model_fetch(self):
        model1, model2, model3 = AssistedTaggingModelFactory.create_batch(3)
        model1_v1 = AssistedTaggingModelVersionFactory.create(model=model1, version='v1.0.0')
        model1_v1_1 = AssistedTaggingModelVersionFactory.create(model=model1, version='v1.0.1')
        model2_v1 = AssistedTaggingModelVersionFactory.create(model=model2, version='v1.0.0')
        model3_v0_1 = AssistedTaggingModelVersionFactory.create(model=model2, version='v0.0.1')
        model3_v1 = AssistedTaggingModelVersionFactory.create(model=model3, version='v1.0.0')
        latest_models = list(AssistedTaggingModelVersion.get_latest_models_version())
        assert model1_v1 not in latest_models
        assert model3_v0_1 not in latest_models
        assert set(latest_models) == set([
            model1_v1_1,
            model2_v1,
            model3_v1,
        ])

    def test_get_existing_draft_entry(self):
        # Model
        model1, model2, model3 = AssistedTaggingModelFactory.create_batch(3)
        # Model Versions
        model1_v1 = AssistedTaggingModelVersionFactory.create(model=model1, version='v1.0.0')
        model1_v1_1 = AssistedTaggingModelVersionFactory.create(model=model1, version='v1.0.1')
        model2_v1 = AssistedTaggingModelVersionFactory.create(model=model2, version='v1.0.0')

        project = ProjectFactory.create()
        lead = LeadFactory.create(project=project)
        excerpt = 'test-101'
        draft_entry1 = DraftEntryFactory.create(project=project, lead=lead, excerpt=excerpt)
        category1, tag1 = AssistedTaggingModelPredictionTagFactory.create_batch(2)

        prediction_common_params = dict(
            draft_entry=draft_entry1,
            category=category1,
            tag=tag1,
            prediction=0.1,
            threshold=0.05,
            is_selected=True,
        )

        # Create predictions with old + latest versions
        AssistedTaggingPredictionFactory.create(
            data_type=AssistedTaggingPrediction.DataType.TAG,
            model_version=model1_v1,
            **prediction_common_params,
        )
        AssistedTaggingPredictionFactory.create(
            data_type=AssistedTaggingPrediction.DataType.TAG,
            model_version=model2_v1,
            **prediction_common_params,
        )

        assert DraftEntry.get_existing_draft_entry(
            project,
            lead,
            excerpt=excerpt,
        ) is None

        # Clear out predictions
        draft_entry1.predictions.all().delete()
        # Create predictions with latest versions only
        AssistedTaggingPredictionFactory.create(
            data_type=AssistedTaggingPrediction.DataType.TAG,
            model_version=model1_v1_1,
            **prediction_common_params,
        )
        AssistedTaggingPredictionFactory.create(
            data_type=AssistedTaggingPrediction.DataType.TAG,
            model_version=model2_v1,
            **prediction_common_params,
        )
        assert DraftEntry.get_existing_draft_entry(
            project,
            lead,
            excerpt=excerpt,
        ) == draft_entry1
