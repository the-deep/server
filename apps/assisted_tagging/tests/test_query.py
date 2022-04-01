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
              group
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
              group
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
                group=tag.group,
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
            group=tag1.group,
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
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '102': {
            'label': 'Cross',
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '103': {
            'label': 'Education',
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '104': {
            'label': 'Food Security',
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '105': {
            'label': 'Health',
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '106': {
            'label': 'Livelihoods',
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '107': {
            'label': 'Logistics',
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '108': {
            'label': 'Nutrition',
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '109': {
            'label': 'Protection',
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '110': {
            'label': 'Shelter',
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '111': {
            'label': 'WASH',
            'group': 'Sectors',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '1',
        },
        '201': {
            'label': 'Environment',
            'group': 'Context',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '202': {
            'label': 'Socio Cultural',
            'group': 'Context',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '203': {
            'label': 'Economy',
            'group': 'Context',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '204': {
            'label': 'Demography',
            'group': 'Context',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '205': {
            'label': 'Legal & Policy',
            'group': 'Context',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '206': {
            'label': 'Security & Stability',
            'group': 'Context',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '207': {
            'label': 'Politics',
            'group': 'Context',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '208': {
            'label': 'Type And Characteristics',
            'group': 'Shock/Event',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '209': {
            'label': 'Underlying/Aggravating Factors',
            'group': 'Shock/Event',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '210': {
            'label': 'Hazard & Threats',
            'group': 'Shock/Event',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '212': {
            'label': 'Type/Numbers/Movements',
            'group': 'Displacement',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '213': {
            'label': 'Push Factors',
            'group': 'Displacement',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '214': {
            'label': 'Pull Factors',
            'group': 'Displacement',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '215': {
            'label': 'Intentions',
            'group': 'Displacement',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '216': {
            'label': 'Local Integration',
            'group': 'Displacement',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '217': {
            'label': 'Injured',
            'group': 'Casualties',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '218': {
            'label': 'Missing',
            'group': 'Casualties',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '219': {
            'label': 'Dead',
            'group': 'Casualties',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '220': {
            'label': 'Relief To Population',
            'group': 'Humanitarian Access',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '221': {
            'label': 'Population To Relief',
            'group': 'Humanitarian Access',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '222': {
            'label': 'Physical Constraints',
            'group': 'Humanitarian Access',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '223': {
            'label': 'Number Of People Facing Humanitarian Access Constraints/Humanitarian Access Gaps',
            'group': 'Humanitarian Access',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '224': {
            'label': 'Communication Means And Preferences',
            'group': 'Information And Communication',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '225': {
            'label': 'Information Challenges And Barriers',
            'group': 'Information And Communication',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '226': {
            'label': 'Knowledge And Info Gaps (Pop)',
            'group': 'Information And Communication',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '227': {
            'label': 'Knowledge And Info Gaps (Hum)',
            'group': 'Information And Communication',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '228': {
            'label': 'Cases',
            'group': 'Covid-19',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '229': {
            'label': 'Contact Tracing',
            'group': 'Covid-19',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '230': {
            'label': 'Deaths',
            'group': 'Covid-19',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '231': {
            'label': 'Hospitalization & Care',
            'group': 'Covid-19',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '232': {
            'label': 'Restriction Measures',
            'group': 'Covid-19',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '233': {
            'label': 'Testing',
            'group': 'Covid-19',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '234': {
            'label': 'Vaccination',
            'group': 'Covid-19',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '2',
        },
        '301': {
            'label': 'Number Of People At Risk',
            'group': 'At Risk',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '302': {
            'label': 'Risk And Vulnerabilities',
            'group': 'At Risk',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '303': {
            'label': 'International Response',
            'group': 'Capacities & Response',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '304': {
            'label': 'Local Response',
            'group': 'Capacities & Response',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '305': {
            'label': 'National Response',
            'group': 'Capacities & Response',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '306': {
            'label': 'Number Of People Reached/Response Gaps',
            'group': 'Capacities & Response',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '307': {
            'label': 'Coping Mechanisms',
            'group': 'Humanitarian Conditions',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '308': {
            'label': 'Living Standards',
            'group': 'Humanitarian Conditions',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '309': {
            'label': 'Number Of People In Need',
            'group': 'Humanitarian Conditions',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '310': {
            'label': 'Physical And Mental Well Being',
            'group': 'Humanitarian Conditions',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '311': {
            'label': 'Driver/Aggravating Factors',
            'group': 'Impact',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '312': {
            'label': 'Impact On People',
            'group': 'Impact',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '313': {
            'label': 'Impact On Systems, Services And Networks',
            'group': 'Impact',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '314': {
            'label': 'Number Of People Affected',
            'group': 'Impact',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '315': {
            'label': 'Expressed By Humanitarian Staff',
            'group': 'Priority Interventions',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '316': {
            'label': 'Expressed By Population',
            'group': 'Priority Interventions',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '317': {
            'label': 'Expressed By Humanitarian Staff',
            'group': 'Priority Needs',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '318': {
            'label': 'Expressed By Population',
            'group': 'Priority Needs',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '3',
        },
        '401': {
            'label': 'Child Head of Household',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '402': {
            'label': 'Chronically Ill',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '403': {
            'label': 'Elderly Head of Household',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '404': {
            'label': 'Female Head of Household',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '405': {
            'label': 'GBV survivors',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '406': {
            'label': 'Indigenous people',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '407': {
            'label': 'LGBTQI+',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '408': {
            'label': 'Minorities',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '409': {
            'label': 'Persons with Disability',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '410': {
            'label': 'Pregnant or Lactating Women',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '411': {
            'label': 'Single Women (including Widows)',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '412': {
            'label': 'Unaccompanied or Separated Children',
            'group': 'Specific Needs Group',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '4',
        },
        '901': {
            'label': 'Infants/Toddlers (<5 years old) ',
            'group': 'Demographic Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '9',
        },
        '902': {
            'label': 'Female Children/Youth (5 to 17 years old)',
            'group': 'Demographic Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '9',
        },
        '903': {
            'label': 'Male Children/Youth (5 to 17 years old)',
            'group': 'Demographic Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '9',
        },
        '904': {
            'label': 'Female Adult (18 to 59 years old)',
            'group': 'Demographic Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '9',
        },
        '905': {
            'label': 'Male Adult (18 to 59 years old)',
            'group': 'Demographic Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '9',
        },
        '906': {
            'label': 'Female Older Persons (60+ years old)',
            'group': 'Demographic Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '9',
        },
        '907': {
            'label': 'Male Older Persons (60+ years old)',
            'group': 'Demographic Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '9',
        },
        '701': {
            'label': 'Critical',
            'group': 'Severity',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '7',
        },
        '702': {
            'label': 'Major',
            'group': 'Severity',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '7',
        },
        '703': {
            'label': 'Minor Problem',
            'group': 'Severity',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '7',
        },
        '704': {
            'label': 'No problem',
            'group': 'Severity',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '7',
        },
        '705': {
            'label': 'Of Concern',
            'group': 'Severity',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '7',
        },
        '801': {
            'label': 'Asylum Seekers',
            'group': 'Affected Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '8',
        },
        '802': {
            'label': 'Host',
            'group': 'Affected Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '8',
        },
        '803': {
            'label': 'IDP',
            'group': 'Affected Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '8',
        },
        '804': {
            'label': 'Migrants',
            'group': 'Affected Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '8',
        },
        '805': {
            'label': 'Refugees',
            'group': 'Affected Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '8',
        },
        '806': {
            'label': 'Returnees',
            'group': 'Affected Groups',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '8',
        },
        '1001': {
            'label': 'Completely reliable',
            'group': 'Reliability',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '10',
        },
        '1002': {
            'label': 'Usually reliable',
            'group': 'Reliability',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '10',
        },
        '1003': {
            'label': 'Fairly Reliable',
            'group': 'Reliability',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '10',
        },
        '1004': {
            'label': 'Unreliable',
            'group': 'Reliability',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '10',
        },
        '501': {
            'label': 'Female',
            'group': 'Gender',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '5',
        },
        '502': {
            'label': 'Male',
            'group': 'Gender',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '5',
        },
        '601': {
            'label': 'Adult (18 to 59 years old)',
            'group': 'Age',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '6',
        },
        '602': {
            'label': 'Children/Youth (5 to 17 years old)',
            'group': 'Age',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '6',
        },
        '603': {
            'label': 'Infants/Toddlers (<5 years old)',
            'group': 'Age',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '6',
        },
        '604': {
            'label': 'Older Persons (60+ years old)',
            'group': 'Age',
            'hide_in_analysis_framework_mapping': False,
            'is_category': False,
            'parent_id': '6',
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
                    'group',
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
