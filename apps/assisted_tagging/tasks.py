from functools import reduce

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db import transaction, models
from django.utils.encoding import DjangoUnicodeDecodeError
from celery import shared_task

from utils.common import redis_lock, UidBase64Helper
from deep.exceptions import DeepBaseException

from .models import (
    DraftEntry,
    AssistedTaggingModel,
    AssistedTaggingModelVersion,
    AssistedTaggingModelPredictionTag,
    AssistedTaggingPrediction,
)
from .token import draft_entry_extraction_token_generator


class AsssistedTaggingTask():
    class Exception():
        class InvalidTokenValue(DeepBaseException):
            default_message = 'Invalid Token'

        class InvalidOrExpiredToken(DeepBaseException):
            default_message = 'Invalid/expired token in client_id'

        class DraftEntryNotFound(DeepBaseException):
            default_message = 'No draft entry found for provided id'

    @staticmethod
    def get_callback_url():
        return (
            settings.DEEPL_SERVICE_CALLBACK_DOMAIN +
            reverse('assisted_tagging_draft_entry_prediction_callback', kwargs={'version': 'v1'})
        )

    @staticmethod
    def generate_draft_entry_client_id(draft_entry: DraftEntry) -> str:
        uid = UidBase64Helper.encode(draft_entry.pk)
        token = draft_entry_extraction_token_generator.make_token(draft_entry)
        return f'{uid}-{token}'

    @classmethod
    def get_draft_entry_from_client_id(cls, client_id):
        try:
            uidb64, token = client_id.split('-', 1)
            uid = UidBase64Helper.decode(uidb64)
        except (ValueError, DjangoUnicodeDecodeError):
            raise cls.Exception.InvalidTokenValue()
        if (draft_entry := DraftEntry.objects.filter(id=uid).first()) is None:
            raise cls.Exception.DraftEntryNotFound(f'No draft entry found for provided id: {uid}')
        if not draft_entry_extraction_token_generator.check_token(draft_entry, token):
            raise cls.Exception.InvalidOrExpiredToken()
        return draft_entry

    # --- Callback logics
    @staticmethod
    def get_or_create_models_version(models_data):
        def get_versions_map():
            return {
                (model_version.model.model_id, model_version.version): model_version
                for model_version in AssistedTaggingModelVersion.objects.filter(
                    reduce(
                        lambda acc, item: acc | item,
                        [
                            models.Q(
                                model__model_id=model_data['id'],
                                version=model_data['version'],
                            )
                            for model_data in models_data
                        ],
                    )
                ).select_related('model').all()
            }

        existing_model_versions = get_versions_map()
        new_model_versions = [
            model_data
            for model_data in models_data
            if (model_data['id'], model_data['version']) not in existing_model_versions
        ]

        if new_model_versions:
            AssistedTaggingModelVersion.objects.bulk_create([
                AssistedTaggingModelVersion(
                    model=AssistedTaggingModel.objects.get_or_create(
                        model_id=model_data['id'],
                        defaults=dict(
                            name=model_data['id'],
                        ),
                    )[0],
                    version=model_data['version'],
                )
                for model_data in models_data
            ])
            existing_model_versions = get_versions_map()
        return existing_model_versions

    @classmethod
    def get_or_create_tags_map(cls, tags):
        def get_tags_map():
            return {
                tag_id: _id
                for _id, tag_id in AssistedTaggingModelPredictionTag.objects.values_list('id', 'tag_id')
            }

        current_tags_map = get_tags_map()
        # Check if new tags needs to be created
        new_tags = [
            tag for tag in tags
            if tag not in current_tags_map
        ]
        if new_tags:
            # Create new tags
            AssistedTaggingModelPredictionTag.objects.bulk_create([
                AssistedTaggingModelPredictionTag(
                    name=new_tag,
                    tag_id=new_tag,
                )
                for new_tag in new_tags
            ])
            # Refetch
            current_tags_map = get_tags_map()
            sync_tags_with_deepl.delay(new_tags)
        return current_tags_map

    @classmethod
    def _process_model_preds(cls, model_version, current_tags_map, draft_entry, model_prediction):
        prediction_status = model_prediction['prediction_status']
        draft_entry.prediction_status = DraftEntry.PredictionStatus.DONE
        if prediction_status == 0:  # If 0 no tags are provided
            return

        tags = model_prediction.get('tags', {})  # NLP TagId
        values = model_prediction.get('values', [])  # Raw value
        print(model_prediction.keys())

        common_attrs = dict(
            model_version=model_version,
            draft_entry_id=draft_entry.id,
        )
        new_predictions = []
        for category_tag, tags in tags.items():
            for tag, prediction_data in tags.items():
                prediction_value = prediction_data.get('prediction')
                threshold_value = prediction_data.get('prediction')
                is_selected = prediction_data.get('is_selected', False)
                new_predictions.append(
                    AssistedTaggingPrediction(
                        **common_attrs,
                        data_type=AssistedTaggingPrediction.DataType.TAG,
                        category_id=current_tags_map[category_tag],
                        tag_id=current_tags_map[tag],
                        prediction=prediction_value,
                        threshold=threshold_value,
                        is_selected=is_selected,
                    )
                )

        for value in set(values):
            new_predictions.append(
                AssistedTaggingPrediction(
                    **common_attrs,
                    data_type=AssistedTaggingPrediction.DataType.RAW,
                    value=value,
                    is_selected=True,
                )
            )
        AssistedTaggingPrediction.objects.bulk_create(new_predictions)

    @classmethod
    def save_entry_draft_data(cls, draft_entry, data):
        model_preds = data['model_preds']
        # Save if new tags are provided
        current_tags_map = cls.get_or_create_tags_map([
            tag
            for prediction in model_preds
            for category_tag, tags in prediction.get('tags', {}).items()
            for tag in [
                category_tag,
                *tags.keys(),
            ]
        ])
        models_version_map = cls.get_or_create_models_version([
            predition['model_info']
            for predition in model_preds
        ])

        with transaction.atomic():
            draft_entry.clear_data()  # Clear old data if exists
            draft_entry.calculated_at = timezone.now()
            for predition in model_preds:
                model_version = models_version_map[(predition['model_info']['id'], predition['model_info']['version'])]
                cls._process_model_preds(model_version, current_tags_map, draft_entry, predition)
            draft_entry.save()
        return draft_entry


@shared_task
@redis_lock('sync_tags_with_deepl', 60 * 60 * 0.5)
def sync_tags_with_deepl(new_tags):
    # TODO:
    print(new_tags)
