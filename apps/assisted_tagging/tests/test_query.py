from unittest.mock import patch
from snapshottest.django import TestCase as SnapShotTextCase

from utils.graphene.tests import GraphQLTestCase

from deep.tests import TestCase
from assisted_tagging.models import (
    AssistedTaggingPrediction,
)

from assisted_tagging.tasks import AsssistedTaggingTask, _sync_tags_with_deepl
from assisted_tagging.models import (
    AssistedTaggingModel,
    AssistedTaggingModelVersion,
    AssistedTaggingModelPredictionTag,
    DraftEntry,
)

from lead.factories import LeadFactory
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
            predictionTags {
              id
              isCategory
              isDeprecated
              hideInAnalysisFrameworkMapping
              parentTag
              tagId
            }
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
            predictionTag(id: $predictionTag) {
              id
              isCategory
              isDeprecated
              hideInAnalysisFrameworkMapping
              parentTag
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
                  modelVersionDeeplModelId
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
        self.assertEqual(content['predictionTags'], [
            dict(
                id=str(tag.id),
                tagId=tag.tag_id,
                isDeprecated=tag.is_deprecated,
                isCategory=tag.is_category,
                hideInAnalysisFrameworkMapping=tag.hide_in_analysis_framework_mapping,
                parentTag=tag.parent_tag_id and str(tag.parent_tag_id),
            )
            for tag in [tag1, *other_tags]
        ])
        self.assertEqual(content['predictionTag'], dict(
            id=str(tag1.id),
            tagId=tag1.tag_id,
            isDeprecated=tag1.is_deprecated,
            isCategory=tag1.is_category,
            hideInAnalysisFrameworkMapping=tag1.hide_in_analysis_framework_mapping,
            parentTag=tag1.parent_tag_id and str(tag1.parent_tag_id),
        ))

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
                    for model_version in _model.versions.all()
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
        lead = LeadFactory.create(project=project)
        user = UserFactory.create()
        another_user = UserFactory.create()
        project.add_member(user)

        model1 = AssistedTaggingModelFactory.create()
        latest_model1_version = AssistedTaggingModelVersionFactory.create_batch(2, model=model1)[0]
        category1, tag1, *other_tags = AssistedTaggingModelPredictionTagFactory.create_batch(5)

        draft_entry1 = DraftEntryFactory.create(project=project, lead=lead, excerpt='sample excerpt')

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
                    modelVersionDeeplModelId=str(prediction1.model_version.model.model_id),
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
                    modelVersionDeeplModelId=str(prediction2.model_version.model.model_id),
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
        'client_id': 'random-client-id',
        'model_preds': [
            {
                'tags': {
                    '1': {
                        '101': {
                            'prediction': 0.0013131533306455466,
                            'threshold': 0.41000000000000003,
                            'is_selected': False,
                        },
                        '103': {
                            'prediction': 0.003010824160731357,
                            'threshold': 0.46,
                            'is_selected': False,
                        },
                        '104': {
                            'prediction': 0.002566287973119567,
                            'threshold': 0.48,
                            'is_selected': False,
                        },
                        '105': {
                            'prediction': 2.677955230077108,
                            'threshold': 0.36,
                            'is_selected': True,
                        },
                        '106': {
                            'prediction': 0.01722483797685096,
                            'threshold': 0.38,
                            'is_selected': False,
                        },
                        '107': {
                            'prediction': 0.003670748323202133,
                            'threshold': 0.5,
                            'is_selected': False,
                        },
                        '108': {
                            'prediction': 0.0041013412481668045,
                            'threshold': 0.49,
                            'is_selected': False,
                        },
                        '109': {
                            'prediction': 0.028100471686700296,
                            'threshold': 0.58,
                            'is_selected': False,
                        },
                        '110': {
                            'prediction': 0.0035644680749447573,
                            'threshold': 0.42,
                            'is_selected': False,
                        },
                        '111': {
                            'prediction': 0.00885658950175879,
                            'threshold': 0.53,
                            'is_selected': False,
                        }
                    },
                    '3': {
                        '301': {
                            'prediction': 0.00023104241032948875,
                            'threshold': 0.12,
                            'is_selected': False,
                        },
                        '302': {
                            'prediction': 0.006840221311261014,
                            'threshold': 0.41000000000000003,
                            'is_selected': False,
                        },
                        '303': {
                            'prediction': 1.51390548675291,
                            'threshold': 0.62,
                            'is_selected': True,
                        },
                        '304': {
                            'prediction': 0.0024619154282845557,
                            'threshold': 0.1,
                            'is_selected': False,
                        },
                        '305': {
                            'prediction': 0.19748103480006374,
                            'threshold': 0.43,
                            'is_selected': False,
                        },
                        '306': {
                            'prediction': 0.1326687938096572,
                            'threshold': 0.49,
                            'is_selected': False,
                        },
                        '307': {
                            'prediction': 0.008473951473004289,
                            'threshold': 0.36,
                            'is_selected': False,
                        },
                        '308': {
                            'prediction': 0.014394345796770519,
                            'threshold': 0.45,
                            'is_selected': False,
                        },
                        '309': {
                            'prediction': 0.002753498941479671,
                            'threshold': 0.31,
                            'is_selected': False,
                        },
                        '310': {
                            'prediction': 0.02261752535293742,
                            'threshold': 0.41000000000000003,
                            'is_selected': False,
                        },
                        '311': {
                            'prediction': 0.0028069927602222093,
                            'threshold': 0.38,
                            'is_selected': False,
                        },
                        '312': {
                            'prediction': 0.0035386373796923594,
                            'threshold': 0.33,
                            'is_selected': False,
                        },
                        '313': {
                            'prediction': 0.00474455507679118,
                            'threshold': 0.45,
                            'is_selected': False,
                        },
                        '314': {
                            'prediction': 0.002435182492869596,
                            'threshold': 0.24,
                            'is_selected': False,
                        },
                        '315': {
                            'prediction': 0.004984116689725355,
                            'threshold': 0.55,
                            'is_selected': False,
                        },
                        '316': {
                            'prediction': 0.0034277827944606543,
                            'threshold': 0.15,
                            'is_selected': False,
                        },
                        '317': {
                            'prediction': 0.0018360981872926156,
                            'threshold': 0.3,
                            'is_selected': False,
                        },
                        '318': {
                            'prediction': 0.007651697378605604,
                            'threshold': 0.25,
                            'is_selected': False,
                        }
                    },
                    '2': {
                        '219': {
                            'prediction': 0.0018779816205746359,
                            'threshold': 0.28,
                            'is_selected': False,
                        },
                        '217': {
                            'prediction': 0.0009131004424908987,
                            'threshold': 0.13,
                            'is_selected': False,
                        },
                        '218': {
                            'prediction': 0.0010629182305330266,
                            'threshold': 0.13,
                            'is_selected': False,
                        },
                        '204': {
                            'prediction': 0.01951472795739466,
                            'threshold': 0.49,
                            'is_selected': False,
                        },
                        '203': {
                            'prediction': 0.002760568168014288,
                            'threshold': 0.41000000000000003,
                            'is_selected': False,
                        },
                        '201': {
                            'prediction': 0.001610475469772753,
                            'threshold': 0.38,
                            'is_selected': False,
                        },
                        '205': {
                            'prediction': 0.0028414463984870143,
                            'threshold': 0.31,
                            'is_selected': False,
                        },
                        '207': {
                            'prediction': 0.0030019306965793175,
                            'threshold': 0.3,
                            'is_selected': False,
                        },
                        '206': {
                            'prediction': 0.0028423364380035887,
                            'threshold': 0.44,
                            'is_selected': False,
                        },
                        '202': {
                            'prediction': 0.0024926103993921592,
                            'threshold': 0.17,
                            'is_selected': False,
                        },
                        '228': {
                            'prediction': 0.004972799797542393,
                            'threshold': 0.8,
                            'is_selected': False,
                        },
                        '229': {
                            'prediction': 0.00032880847216941987,
                            'threshold': 0.39,
                            'is_selected': False,
                        },
                        '230': {
                            'prediction': 0.001167356436152333,
                            'threshold': 0.81,
                            'is_selected': False,
                        },
                        '231': {
                            'prediction': 0.0024493522487762497,
                            'threshold': 0.41000000000000003,
                            'is_selected': False,
                        },
                        '232': {
                            'prediction': 0.005428578056718992,
                            'threshold': 0.46,
                            'is_selected': False,
                        },
                        '233': {
                            'prediction': 0.0018874364551392537,
                            'threshold': 0.79,
                            'is_selected': False,
                        },
                        '234': {
                            'prediction': 0.0011778841898949057,
                            'threshold': 0.54,
                            'is_selected': False,
                        },
                        '215': {
                            'prediction': 0.0004781786533146116,
                            'threshold': 0.38,
                            'is_selected': False,
                        },
                        '216': {
                            'prediction': 0.006963967811316252,
                            'threshold': 0.25,
                            'is_selected': False,
                        },
                        '214': {
                            'prediction': 0.0003674881209635401,
                            'threshold': 0.29,
                            'is_selected': False,
                        },
                        '213': {
                            'prediction': 0.0002446720680234501,
                            'threshold': 0.37,
                            'is_selected': False,
                        },
                        '212': {
                            'prediction': 0.012378716890357043,
                            'threshold': 0.38,
                            'is_selected': False,
                        },
                        '223': {
                            'prediction': 0.001155513591390658,
                            'threshold': 0.47000000000000003,
                            'is_selected': False,
                        },
                        '222': {
                            'prediction': 0.0014652756362920627,
                            'threshold': 0.48,
                            'is_selected': False,
                        },
                        '221': {
                            'prediction': 0.001666667767016119,
                            'threshold': 0.19,
                            'is_selected': False,
                        },
                        '220': {
                            'prediction': 0.011259256380385366,
                            'threshold': 0.29,
                            'is_selected': False,
                        },
                        '224': {
                            'prediction': 0.007581055563475405,
                            'threshold': 0.21,
                            'is_selected': False,
                        },
                        '225': {
                            'prediction': 0.0003372832482758289,
                            'threshold': 0.15,
                            'is_selected': False,
                        },
                        '227': {
                            'prediction': 0.0009009759297542688,
                            'threshold': 0.18,
                            'is_selected': False,
                        },
                        '226': {
                            'prediction': 0.0007702910806983709,
                            'threshold': 0.18,
                            'is_selected': False,
                        },
                        '210': {
                            'prediction': 0.006979638609387304,
                            'threshold': 0.23,
                            'is_selected': False,
                        },
                        '208': {
                            'prediction': 0.00357941840775311,
                            'threshold': 0.2,
                            'is_selected': False,
                        },
                        '209': {
                            'prediction': 0.006321697112391976,
                            'threshold': 0.17,
                            'is_selected': False,
                        }
                    },
                    '6': {
                        '601': {
                            'prediction': 0.04068703080217044,
                            'threshold': 0.48,
                            'is_selected': True,
                        },
                        '602': {
                            'prediction': 0.024587836709212173,
                            'threshold': 0.44,
                            'is_selected': False,
                        },
                        '603': {
                            'prediction': 0.04259871318936348,
                            'threshold': 0.4,
                            'is_selected': False,
                        },
                        '604': {
                            'prediction': 0.006414494919972342,
                            'threshold': 0.61,
                            'is_selected': False,
                        }
                    },
                    '5': {
                        '501': {
                            'prediction': 1.403369450233352,
                            'threshold': 0.71,
                            'is_selected': True,
                        },
                        '502': {
                            'prediction': 0.007781315997073596,
                            'threshold': 0.44,
                            'is_selected': False,
                        }
                    },
                    '8': {
                        '801': {
                            'prediction': 0.0002758237987769487,
                            'threshold': 0.73,
                            'is_selected': False,
                        },
                        '802': {
                            'prediction': 0.00997524285181002,
                            'threshold': 0.55,
                            'is_selected': False,
                        },
                        '803': {
                            'prediction': 0.004761773787105261,
                            'threshold': 0.67,
                            'is_selected': False,
                        },
                        '804': {
                            'prediction': 0.000846206055333217,
                            'threshold': 0.75,
                            'is_selected': False,
                        },
                        '805': {
                            'prediction': 0.0007048035968182376,
                            'threshold': 0.64,
                            'is_selected': False,
                        },
                        '806': {
                            'prediction': 0.007033202674169585,
                            'threshold': 0.53,
                            'is_selected': False,
                        }
                    },
                    '4': {
                        '401': {
                            'prediction': 0.0002081420534523204,
                            'threshold': 0.25,
                            'is_selected': False,
                        },
                        '402': {
                            'prediction': 0.0029977605726312978,
                            'threshold': 0.58,
                            'is_selected': False,
                        },
                        '403': {
                            'prediction': 0.0029921820636705627,
                            'threshold': 0.14,
                            'is_selected': False,
                        },
                        '404': {
                            'prediction': 0.002415977602746959,
                            'threshold': 0.48,
                            'is_selected': False,
                        },
                        '405': {
                            'prediction': 0.020530499899998687,
                            'threshold': 0.78,
                            'is_selected': False,
                        },
                        '406': {
                            'prediction': 0.0028101496774559985,
                            'threshold': 0.13,
                            'is_selected': False,
                        },
                        '407': {
                            'prediction': 0.00022843408415366598,
                            'threshold': 0.41000000000000003,
                            'is_selected': False,
                        },
                        '408': {
                            'prediction': 0.009432899118480036,
                            'threshold': 0.59,
                            'is_selected': False,
                        },
                        '409': {
                            'prediction': 0.000918924031014155,
                            'threshold': 0.56,
                            'is_selected': False,
                        },
                        '410': {
                            'prediction': 2.0397998848739936,
                            'threshold': 0.49,
                            'is_selected': True,
                        },
                        '411': {
                            'prediction': 0.007506779511459172,
                            'threshold': 0.2,
                            'is_selected': False,
                        },
                        '412': {
                            'prediction': 0.00019092757914525768,
                            'threshold': 0.6,
                            'is_selected': False,
                        }
                    },
                    '9': {
                        '904': {
                            'prediction': 0.5,
                            'threshold': 0.5,
                            'is_selected': True,
                        },
                        '905': {
                            'prediction': 0.5,
                            'threshold': 0.5,
                            'is_selected': False,
                        },
                        '902': {
                            'prediction': 0.5,
                            'threshold': 0.5,
                            'is_selected': False,
                        },
                        '903': {
                            'prediction': 0.5,
                            'threshold': 0.5,
                            'is_selected': False,
                        },
                        '906': {
                            'prediction': 0.5,
                            'threshold': 0.5,
                            'is_selected': False,
                        },
                        '907': {
                            'prediction': 0.5,
                            'threshold': 0.5,
                            'is_selected': False,
                        }
                    }
                },
                'prediction_status': 1,
                'model_info': {
                    'id': 'all_tags_model',
                    'version': '1.0.0',
                }
            },
            {
                'model_info': {
                    'id': 'geolocation',
                    'version': '1.0.0',
                },
                'values': [
                    'Nepal',
                    'Paris',
                ],
                'prediction_status': 1
            },
            {
                'model_info': {
                    'id': 'reliability',
                    'version': '1.0.0',
                },
                'tags': {
                    '10': {
                        '1002': {
                            'is_selected': True,
                        }
                    }
                },
                'prediction_status': 1
            }
        ]
    }

    DEEPL_TAGS_MOCK_RESPONSE = {
        '101': {
            'label': 'Agriculture',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '102': {
            'label': 'Cross',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '103': {
            'label': 'Education',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '104': {
            'label': 'Food Security',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '105': {
            'label': 'Health',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '106': {
            'label': 'Livelihoods',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '107': {
            'label': 'Logistics',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '108': {
            'label': 'Nutrition',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '109': {
            'label': 'Protection',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '110': {
            'label': 'Shelter',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '111': {
            'label': 'WASH',
            'is_category': False,
            'parent_id': '1',
            'hide_in_analysis_framework_mapping': False
        },
        '201': {
            'label': 'Context->Environment',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '202': {
            'label': 'Context->Socio Cultural',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '203': {
            'label': 'Context->Economy',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '204': {
            'label': 'Context->Demography',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '205': {
            'label': 'Context->Legal & Policy',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '206': {
            'label': 'Context->Security & Stability',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '207': {
            'label': 'Context->Politics',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '208': {
            'label': 'Shock/Event->Type And Characteristics',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '209': {
            'label': 'Shock/Event->Underlying/Aggravating Factors',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '210': {
            'label': 'Shock/Event->Hazard & Threats',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '212': {
            'label': 'Displacement->Type/Numbers/Movements',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '213': {
            'label': 'Displacement->Push Factors',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '214': {
            'label': 'Displacement->Pull Factors',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '215': {
            'label': 'Displacement->Intentions',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '216': {
            'label': 'Displacement->Local Integration',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '217': {
            'label': 'Casualties->Injured',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '218': {
            'label': 'Casualties->Missing',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '219': {
            'label': 'Casualties->Dead',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '220': {
            'label': 'Humanitarian Access->Relief To Population',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '221': {
            'label': 'Humanitarian Access->Population To Relief',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '222': {
            'label': 'Humanitarian Access->Physical Constraints',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '223': {
            'label': 'Humanitarian Access->Number Of People Facing Humanitarian Access Constraints/Humanitarian Access Gaps',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '224': {
            'label': 'Information And Communication->Communication Means And Preferences',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '225': {
            'label': 'Information And Communication->Information Challenges And Barriers',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '226': {
            'label': 'Information And Communication->Knowledge And Info Gaps (Pop)',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '227': {
            'label': 'Information And Communication->Knowledge And Info Gaps (Hum)',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '228': {
            'label': 'Covid-19->Cases',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '229': {
            'label': 'Covid-19->Contact Tracing',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '230': {
            'label': 'Covid-19->Deaths',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '231': {
            'label': 'Covid-19->Hospitalization & Care',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '232': {
            'label': 'Covid-19->Restriction Measures',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '233': {
            'label': 'Covid-19->Testing',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '234': {
            'label': 'Covid-19->Vaccination',
            'is_category': False,
            'parent_id': '2',
            'hide_in_analysis_framework_mapping': False
        },
        '301': {
            'label': 'At Risk->Number Of People At Risk',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '302': {
            'label': 'At Risk->Risk And Vulnerabilities',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '303': {
            'label': 'Capacities & Response->International Response',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '304': {
            'label': 'Capacities & Response->Local Response',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '305': {
            'label': 'Capacities & Response->National Response',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '306': {
            'label': 'Capacities & Response->Number Of People Reached/Response Gaps',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '307': {
            'label': 'Humanitarian Conditions->Coping Mechanisms',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '308': {
            'label': 'Humanitarian Conditions->Living Standards',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '309': {
            'label': 'Humanitarian Conditions->Number Of People In Need',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '310': {
            'label': 'Humanitarian Conditions->Physical And Mental Well Being',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '311': {
            'label': 'Impact->Driver/Aggravating Factors',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '312': {
            'label': 'Impact->Impact On People',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '313': {
            'label': 'Impact->Impact On Systems, Services And Networks',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '314': {
            'label': 'Impact->Number Of People Affected',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '315': {
            'label': 'Priority Interventions->Expressed By Humanitarian Staff',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '316': {
            'label': 'Priority Interventions->Expressed By Population',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '317': {
            'label': 'Priority Needs->Expressed By Humanitarian Staff',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '318': {
            'label': 'Priority Needs->Expressed By Population',
            'is_category': False,
            'parent_id': '3',
            'hide_in_analysis_framework_mapping': False
        },
        '401': {
            'label': 'Child Head of Household',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '402': {
            'label': 'Chronically Ill',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '403': {
            'label': 'Elderly Head of Household',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '404': {
            'label': 'Female Head of Household',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '405': {
            'label': 'GBV survivors',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '406': {
            'label': 'Indigenous people',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '407': {
            'label': 'LGBTQI+',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '408': {
            'label': 'Minorities',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '409': {
            'label': 'Persons with Disability',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '410': {
            'label': 'Pregnant or Lactating Women',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '411': {
            'label': 'Single Women (including Widows)',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '412': {
            'label': 'Unaccompanied or Separated Children',
            'is_category': False,
            'parent_id': '4',
            'hide_in_analysis_framework_mapping': False
        },
        '901': {
            'label': 'Infants/Toddlers (<5 years old) ',
            'is_category': False,
            'parent_id': '9',
            'hide_in_analysis_framework_mapping': False
        },
        '902': {
            'label': 'Female Children/Youth (5 to 17 years old)',
            'is_category': False,
            'parent_id': '9',
            'hide_in_analysis_framework_mapping': False
        },
        '903': {
            'label': 'Male Children/Youth (5 to 17 years old)',
            'is_category': False,
            'parent_id': '9',
            'hide_in_analysis_framework_mapping': False
        },
        '904': {
            'label': 'Female Adult (18 to 59 years old)',
            'is_category': False,
            'parent_id': '9',
            'hide_in_analysis_framework_mapping': False
        },
        '905': {
            'label': 'Male Adult (18 to 59 years old)',
            'is_category': False,
            'parent_id': '9',
            'hide_in_analysis_framework_mapping': False
        },
        '906': {
            'label': 'Female Older Persons (60+ years old)',
            'is_category': False,
            'parent_id': '9',
            'hide_in_analysis_framework_mapping': False
        },
        '907': {
            'label': 'Male Older Persons (60+ years old)',
            'is_category': False,
            'parent_id': '9',
            'hide_in_analysis_framework_mapping': False
        },
        '701': {
            'label': 'Critical',
            'is_category': False,
            'parent_id': '7',
            'hide_in_analysis_framework_mapping': False
        },
        '702': {
            'label': 'Major',
            'is_category': False,
            'parent_id': '7',
            'hide_in_analysis_framework_mapping': False
        },
        '703': {
            'label': 'Minor Problem',
            'is_category': False,
            'parent_id': '7',
            'hide_in_analysis_framework_mapping': False
        },
        '704': {
            'label': 'No problem',
            'is_category': False,
            'parent_id': '7',
            'hide_in_analysis_framework_mapping': False
        },
        '705': {
            'label': 'Of Concern',
            'is_category': False,
            'parent_id': '7',
            'hide_in_analysis_framework_mapping': False
        },
        '801': {
            'label': 'Asylum Seekers',
            'is_category': False,
            'parent_id': '8',
            'hide_in_analysis_framework_mapping': False
        },
        '802': {
            'label': 'Host',
            'is_category': False,
            'parent_id': '8',
            'hide_in_analysis_framework_mapping': False
        },
        '803': {
            'label': 'IDP',
            'is_category': False,
            'parent_id': '8',
            'hide_in_analysis_framework_mapping': False
        },
        '804': {
            'label': 'Migrants',
            'is_category': False,
            'parent_id': '8',
            'hide_in_analysis_framework_mapping': False
        },
        '805': {
            'label': 'Refugees',
            'is_category': False,
            'parent_id': '8',
            'hide_in_analysis_framework_mapping': False
        },
        '806': {
            'label': 'Returnees',
            'is_category': False,
            'parent_id': '8',
            'hide_in_analysis_framework_mapping': False
        },
        '1001': {
            'label': 'Completely reliable',
            'is_category': False,
            'parent_id': '10',
            'hide_in_analysis_framework_mapping': False
        },
        '1002': {
            'label': 'Usually reliable',
            'is_category': False,
            'parent_id': '10',
            'hide_in_analysis_framework_mapping': False
        },
        '1003': {
            'label': 'Fairly Reliable',
            'is_category': False,
            'parent_id': '10',
            'hide_in_analysis_framework_mapping': False
        },
        '1004': {
            'label': 'Unreliable',
            'is_category': False,
            'parent_id': '10',
            'hide_in_analysis_framework_mapping': False
        },
        '1': {
            'label': 'sectors',
            'is_category': True,
            'hide_in_analysis_framework_mapping': True
        },
        '2': {
            'label': 'subpillars_1d',
            'is_category': True,
            'hide_in_analysis_framework_mapping': True
        },
        '3': {
            'label': 'subpillars_2d',
            'is_category': True,
            'hide_in_analysis_framework_mapping': True
        },
        '6': {
            'label': 'age',
            'is_category': True,
            'hide_in_analysis_framework_mapping': True
        },
        '5': {
            'label': 'gender',
            'is_category': True,
            'hide_in_analysis_framework_mapping': True
        },
        '9': {
            'label': 'demographic_group',
            'is_category': True,
            'hide_in_analysis_framework_mapping': True
        },
        '8': {
            'label': 'affected_groups',
            'is_category': True,
            'hide_in_analysis_framework_mapping': True
        },
        '4': {
            'label': 'specific_needs_groups',
            'is_category': True,
            'hide_in_analysis_framework_mapping': True
        },
        '7': {
            'label': 'severity',
            'is_category': True,
            'hide_in_analysis_framework_mapping': True
        },
        '10': {
            'label': 'reliability',
            'is_category': True,
            'hide_in_analysis_framework_mapping': True
        },
        '501': {
            'label': 'Female',
            'is_category': False,
            'parent_id': '5',
            'hide_in_analysis_framework_mapping': True
        },
        '502': {
            'label': 'Male',
            'is_category': False,
            'parent_id': '5',
            'hide_in_analysis_framework_mapping': True
        },
        '601': {
            'label': 'Adult (18 to 59 years old)',
            'is_category': False,
            'parent_id': '6',
            'hide_in_analysis_framework_mapping': True
        },
        '602': {
            'label': 'Children/Youth (5 to 17 years old)',
            'is_category': False,
            'parent_id': '6',
            'hide_in_analysis_framework_mapping': True
        },
        '603': {
            'label': 'Infants/Toddlers (<5 years old)',
            'is_category': False,
            'parent_id': '6',
            'hide_in_analysis_framework_mapping': True
        },
        '604': {
            'label': 'Older Persons (60+ years old)',
            'is_category': False,
            'parent_id': '6',
            'hide_in_analysis_framework_mapping': True
        }
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
                    AssistedTaggingModelPredictionTag.objects.values('name', 'tag_id', 'is_deprecated')
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
        project = ProjectFactory.create()
        lead = LeadFactory.create(project=project)
        draft_args = dict(
            project=project,
            lead=lead,
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

    @patch('assisted_tagging.tasks.requests')
    def test_tags_sync(self, sync_request_mock):
        def _get_current_tags():
            return list(
                AssistedTaggingModelPredictionTag.objects.values(
                    'name',
                    'tag_id',
                    'is_deprecated',
                    'is_category',
                    'hide_in_analysis_framework_mapping',
                    'parent_tag__tag_id',
                ).order_by('tag_id')
            )

        self.maxDiff = None
        sync_request_mock.get.return_value.status_code = 200
        sync_request_mock.get.return_value.json.return_value = self.DEEPL_TAGS_MOCK_RESPONSE
        self.assertEqual(len(_get_current_tags()), 0)
        _sync_tags_with_deepl()
        self.assertNotEqual(len(_get_current_tags()), 0)
        self.assertMatchSnapshot(_get_current_tags(), 'sync-tags')
