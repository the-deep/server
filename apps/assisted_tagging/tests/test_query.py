from snapshottest.django import TestCase as SnapShotTextCase

from utils.graphene.tests import GraphQLTestCase

from deep.tests import TestCase
from assisted_tagging.models import (
    AssistedTaggingPrediction,
)

from assisted_tagging.tasks import AsssistedTaggingTask
from assisted_tagging.models import (
    AssistedTaggingModel,
    AssistedTaggingModelVersion,
    AssistedTaggingModelPredictionTag,
    DraftEntry,
)
from user.factories import UserFactory
from project.factories import ProjectFactory

from assisted_tagging.factories import (
    AssistedTaggingModelFactory,
    AssistedTaggingModelPredictionTagFactory,
    AssistedTaggingModelVersionFactory,
    DraftEntryFactory,
    AssistedTaggingPredictionFactory,
    MissingPredictionReviewFactory,
    WrongPredictionReviewFactory,
)


class TestAssistedTaggingQuery(GraphQLTestCase):
    ENABLE_NOW_PATCHER = True

    ASSISTED_TAGGING_NLP_DATA = '''
        query MyQuery ($taggingModelId: ID!, $predictionTag: ID!) {
          assistedTagging {
            predictionTags(ordering: ASC_ID) {
              totalCount
              results {
                id
                isDepricated
                tagId
              }
            }
            taggingModels(ordering: ASC_ID) {
              totalCount
              results {
                id
                modelId
                name
                latestVersion {
                    id
                    version
                }
                versions {
                  id
                  version
                }
              }
            }
            taggingModel(id: $taggingModelId) {
              id
              modelId
              name
              latestVersion {
                  id
                  version
              }
              versions {
                id
                version
              }
            }
            predictionTag(id: $predictionTag) {
              id
              isDepricated
              tagId
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
                predictions {
                  id
                  modelVersion
                  dataType
                  dataTypeDisplay
                  value
                  category
                  tag
                  wrongPredictionReviews {
                    id
                  }
                }
                missingPredictionReviews {
                  id
                  category
                  tag
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
        tag1, *other_tags = AssistedTaggingModelPredictionTagFactory.create_batch(5)

        # -- without login
        content = self.query_check(
            self.ASSISTED_TAGGING_NLP_DATA,
            variables=dict(
                taggingModelId=model1.id,
                predictionTag=tag1.id,
            ),
            assert_for_error=True,
        )

        # -- with login
        self.force_login(user)
        content = self.query_check(
            self.ASSISTED_TAGGING_NLP_DATA,
            variables=dict(
                taggingModelId=model1.id,
                predictionTag=tag1.id,
            )
        )['data']['assistedTagging']
        self.assertEqual(content['predictionTags'], dict(
            totalCount=5,
            results=[
                dict(
                    id=str(tag.id),
                    tagId=tag.tag_id,
                    isDepricated=tag.is_depricated,
                )
                for tag in [tag1, *other_tags]
            ],
        ))
        self.assertEqual(content['predictionTag'], dict(
            id=str(tag1.id),
            tagId=tag1.tag_id,
            isDepricated=tag1.is_depricated,
        ))

        self.assertEqual(content['taggingModels'], dict(
            totalCount=2,
            results=[
                dict(
                    id=str(_model.id),
                    modelId=_model.model_id,
                    name=_model.name,
                    latestVersion=_model.latest_version and dict(
                        id=str(_model.latest_version.id),
                        version=str(_model.latest_version.version),
                    ),
                    versions=[
                        dict(
                            id=str(model_version.id),
                            version=str(model_version.version),
                        )
                        for model_version in _model.versions.all()
                    ],
                )
                for _model in [model1, *other_models]
            ],
        ))
        self.assertEqual(content['taggingModel'], dict(
            id=str(model1.id),
            modelId=model1.model_id,
            name=model1.name,
            latestVersion=dict(
                id=str(model1.latest_version.id),
                version=str(model1.latest_version.version),
            ),
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
        user = UserFactory.create()
        another_user = UserFactory.create()
        project.add_member(user)

        model1 = AssistedTaggingModelFactory.create()
        latest_model1_version = AssistedTaggingModelVersionFactory.create_batch(2, model=model1)[0]
        category1, tag1, *other_tags = AssistedTaggingModelPredictionTagFactory.create_batch(5)

        draft_entry1 = DraftEntryFactory.create(project=project, excerpt='sample excerpt')

        prediction1 = AssistedTaggingPredictionFactory.create(
            data_type=AssistedTaggingPrediction.DataType.TAG,
            model_version=latest_model1_version,
            draft_entry=draft_entry1,
            category=category1,
            tag=tag1,
            prediction=0.1,
            threshold=0.05,
            is_selected=True,
        )
        prediction2 = AssistedTaggingPredictionFactory.create(
            data_type=AssistedTaggingPrediction.DataType.RAW,
            model_version=latest_model1_version,
            draft_entry=draft_entry1,
            value='Nepal',
            is_selected=True,
        )
        missing_prediction1 = MissingPredictionReviewFactory.create(
            draft_entry=draft_entry1,
            category=category1,
            tag=other_tags[0],
        )
        wrong_prediction1 = WrongPredictionReviewFactory.create(
            prediction=prediction1,
            created_by=user,
        )

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
            predictions=[
                dict(
                    id=str(prediction1.pk),
                    modelVersion=str(prediction1.model_version_id),
                    dataType=self.genum(prediction1.data_type),
                    dataTypeDisplay=prediction1.get_data_type_display(),
                    value='',
                    category=str(prediction1.category_id),
                    tag=str(prediction1.tag_id),
                    wrongPredictionReviews=[dict(id=str(wrong_prediction1.id))],
                ),
                dict(
                    id=str(prediction2.id),
                    modelVersion=str(prediction2.model_version.id),
                    dataType=self.genum(prediction2.data_type),
                    dataTypeDisplay=prediction2.get_data_type_display(),
                    value="Nepal",
                    category=None,
                    tag=None,
                    wrongPredictionReviews=[],
                )
            ],
            missingPredictionReviews=[
                dict(
                    id=str(missing_prediction1.pk),
                    category=str(missing_prediction1.category_id),
                    tag=str(missing_prediction1.tag_id),
                )
            ]
        ))


class AssistedTaggingCallbackApiTest(TestCase, SnapShotTextCase):

    DEEPL_CALLBACK_MOCK_DATA = {
        "entry_id": "overwrite-this-properly",
        "model_preds": [
            {
                "model_info": {
                    "id": "all_tags_model",
                    "version": "1.0.0"
                },
                "tags": {
                    "category-all-tags-1": {
                        "tag-all-tags-1-1": {
                            "prediction": 0.00011,
                            "threshold": 0.00111,
                            "is_selected": False
                        },
                        "tag-all-tags-1-2": {
                            "prediction": 0.00012,
                            "threshold": 0.00112,
                            "is_selected": False
                        }
                    },
                    "category-all-tags-2": {
                        "tag-all-tags-2-1": {
                            "prediction": 0.00021,
                            "threshold": 0.00221,
                            "is_selected": True
                        },
                        "tag-all-tags-2-2": {
                            "prediction": 0.00022,
                            "threshold": 0.00222,
                            "is_selected": True
                        }
                    }
                },
                "prediction_status": "1"
            },
            {
                "model_info": {
                    "id": "reliability",
                    "version": "1.0.0"
                },
                "tags": {
                    "category-reliability-1": {
                        "tag-reliability-1-1": {
                            "is_selected": False
                        },
                        "tag-reliability-1-2": {
                            "is_selected": True
                        }
                    },
                    "category-reliability-2": {
                        "tag-reliability-2-1": {
                            "is_selected": False
                        },
                        "tag-reliability-2-2": {
                            "is_selected": True
                        }
                    }
                },
                "prediction_status": "1"
            },
            {
                "model_info": {
                    "id": "geolocations",
                    "version": "1.0.0"
                },
                "values": [
                    "Nepal",
                    "Bagmati",
                    "Kathmandu"
                ],
                "prediction_status": "1"
            }
        ]
    }

    def test_save_draft_entry(self):
        def _check_draft_entry_status(draft_entry, status):
            draft_entry.refresh_from_db()
            self.assertEqual(draft_entry.prediction_status, status)

        def _get_current_model_stats():
            return dict(
                model_count=AssistedTaggingModel.objects.count(),
                model_version_count=AssistedTaggingModelVersion.objects.count(),
                tag_count=AssistedTaggingModelPredictionTag.objects.count(),
                models=list(
                    AssistedTaggingModel.objects.values('model_id', 'name')
                ),
                model_versions=list(
                    AssistedTaggingModelVersion.objects.values('model__model_id', 'version')
                ),
                tags=list(
                    AssistedTaggingModelPredictionTag.objects.values('name', 'tag_id', 'is_depricated')
                ),
            )

        def _get_current_prediction_stats():
            return dict(
                prediction_count=AssistedTaggingPrediction.objects.count(),
                predictions=list(
                    AssistedTaggingPrediction.objects.values(
                        'data_type',
                        'model_version__model__model_id',
                        'draft_entry__excerpt',
                        'value',
                        'category__tag_id',
                        'tag__tag_id',
                        'prediction',
                        'threshold',
                        'is_selected',
                    ).order_by(
                        'data_type',
                        'model_version__model__model_id',
                        'draft_entry__excerpt',
                        'value',
                        'category__tag_id',
                        'tag__tag_id',
                        'prediction',
                        'threshold',
                        'is_selected',
                    )
                )
            )

        url = '/api/v1/callback/assisted-tagging-draft-entry-prediction/'
        draft_args = dict(
            project=ProjectFactory.create(),
            prediction_status=DraftEntry.PredictionStatus.STARTED,
        )
        draft_entry1 = DraftEntryFactory.create(
            **draft_args,
            excerpt='sample excerpt 101',
        )
        draft_entry2 = DraftEntryFactory.create(
            **draft_args,
            excerpt='sample excerpt 102',
        )

        # ------ Invalid entry_id
        data = {
            **self.DEEPL_CALLBACK_MOCK_DATA,
            'client_id': 'invalid-id',
        }

        response = self.client.post(url, data)
        self.assert_400(response)
        _check_draft_entry_status(draft_entry1, DraftEntry.PredictionStatus.STARTED)

        # ----- Valid entry_id
        data = {
            **self.DEEPL_CALLBACK_MOCK_DATA,
            'client_id': AsssistedTaggingTask.generate_draft_entry_client_id(draft_entry1),
        }

        self.maxDiff = None
        current_model_stats = _get_current_model_stats()
        current_prediction_stats = _get_current_prediction_stats()
        response = self.client.post(url, data)
        self.assert_200(response)
        self.assertNotEqual(current_model_stats, _get_current_model_stats())
        self.assertNotEqual(current_prediction_stats, _get_current_prediction_stats())
        _check_draft_entry_status(draft_entry1, DraftEntry.PredictionStatus.DONE)

        current_model_stats = _get_current_model_stats()
        current_prediction_stats = _get_current_prediction_stats()
        response = self.client.post(url, data)
        _check_draft_entry_status(draft_entry1, DraftEntry.PredictionStatus.DONE)
        self.assertEqual(current_model_stats, _get_current_model_stats())
        self.assertEqual(current_prediction_stats, _get_current_prediction_stats())

        # ----- Valid entry_id send with same type of data
        data = {
            **self.DEEPL_CALLBACK_MOCK_DATA,
            'client_id': AsssistedTaggingTask.generate_draft_entry_client_id(draft_entry2),
        }

        current_model_stats = _get_current_model_stats()
        response = self.client.post(url, data)
        _check_draft_entry_status(draft_entry2, DraftEntry.PredictionStatus.DONE)
        self.assertEqual(current_model_stats, _get_current_model_stats())
        self.assertNotEqual(current_prediction_stats, _get_current_prediction_stats())

        current_model_stats = _get_current_model_stats()
        current_prediction_stats = _get_current_prediction_stats()
        self.assertMatchSnapshot(current_model_stats, 'final-current-model-stats')
        self.assertMatchSnapshot(current_prediction_stats, 'final-current-prediction-stats')
