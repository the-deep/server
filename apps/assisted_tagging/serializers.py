from django.db import transaction
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer, UserResourceCreatedMixin
from deep.serializers import ProjectPropertySerializerMixin, TempClientIdMixin
from analysis_framework.models import Widget

from .models import (
    DraftEntry,
    MissingPredictionReview,
    PredictionTagAnalysisFrameworkWidgetMapping,
    WrongPredictionReview,
)
from lead.models import Lead
from .tasks import (
    trigger_request_for_draft_entry_task,
    trigger_request_for_auto_draft_entry_task
)


# ---------- Graphql ---------------------------
class DraftEntryBaseSerializer(serializers.Serializer):
    def validate_lead(self, lead):
        if lead.project != self.project:
            raise serializers.ValidationError('Only lead from current project are allowed.')
        af = lead.project.analysis_framework
        if af is None or not af.assisted_tagging_enabled:
            raise serializers.ValidationError('Assisted tagging is disabled for the Framework used by this project.')
        return lead


class DraftEntryGqlSerializer(
    ProjectPropertySerializerMixin,
    DraftEntryBaseSerializer,
    UserResourceCreatedMixin,
    serializers.ModelSerializer,
):
    class Meta:
        model = DraftEntry
        fields = (
            'lead',
            'excerpt',
        )

    def create(self, data):
        # Use already existing draft entry if found
        project = data['lead'].project
        already_existing_draft_entry = DraftEntry.get_existing_draft_entry(
            project,
            data['lead'],
            data['excerpt'],
        )
        if already_existing_draft_entry:
            return already_existing_draft_entry
        # Create new one and send trigger to deepl.
        data['project'] = project
        instance = super().create(data)
        transaction.on_commit(
            lambda: trigger_request_for_draft_entry_task.delay(instance.pk)
        )
        return instance

    def update(self, *_):
        raise Exception("Update is not allowed")


class WrongPredictionReviewGqlSerializer(UserResourceSerializer, serializers.ModelSerializer):
    class Meta:
        model = WrongPredictionReview
        fields = (
            'prediction',
        )

    def validate_prediction(self, prediction):
        if prediction.draft_entry.project != self.context['request'].active_project:
            raise serializers.ValidationError('Prediction not part of the active project.')
        return prediction

    def validate(self, data):
        if self.instance and self.instance.created_by != self.context['request'].user:
            raise serializers.ValidationError('Only reviewer can edit this review')
        return data


class MissingPredictionReviewGqlSerializer(UserResourceSerializer):
    class Meta:
        model = MissingPredictionReview
        fields = (
            'draft_entry',
            'tag',
            'category',
        )

    def validate_draft_entry(self, draft_entry):
        if draft_entry.project != self.context['request'].active_project:
            raise serializers.ValidationError('Draft Entry not part of the active project.')
        return draft_entry

    def validate(self, data):
        if self.instance and self.instance.created_by != self.context['request'].user:
            raise serializers.ValidationError('Only reviewer can edit this review')
        return data


# ------------------------ Analysis Framework ---------------------------------------------
class PredictionTagAnalysisFrameworkMapSerializer(TempClientIdMixin, serializers.ModelSerializer):
    TAG_NOT_REQUIRED_FOR_WIDGET_TYPE = [
        Widget.WidgetType.GEO,
    ]

    class Meta:
        model = PredictionTagAnalysisFrameworkWidgetMapping
        fields = (
            'id',
            'widget',
            'tag',
            'association',
            'client_id',  # From TempClientIdMixin
        )

    def validate(self, data):
        tag = data.get('tag', self.instance and self.instance.tag)
        association = data.get('association', self.instance and self.instance.association)
        widget = data.get('widget', self.instance and self.instance.widget)
        skip_tag = widget.widget_id in self.TAG_NOT_REQUIRED_FOR_WIDGET_TYPE
        if tag is None and not skip_tag:
            raise serializers.ValidationError(dict(
                tag='Tag is required for this widget.'
            ))
        if association is None and not skip_tag:
            raise serializers.ValidationError(dict(
                association='Association is required for this widget.'
            ))
        return data


class TriggerDraftEntryGqlSerializer(
    DraftEntryBaseSerializer,
    ProjectPropertySerializerMixin,
    UserResourceCreatedMixin,
    serializers.ModelSerializer,
):
    class Meta:
        model = DraftEntry
        fields = (
            'lead',
        )

    def create(self, data):
        lead = data['lead']
        if lead.leadpreview.text_extraction_id is None:
            raise serializers.DjangoValidationError("Assisted tagging is not available in old lead")
        if lead.auto_entry_extraction_status == Lead.AutoExtractionStatus.SUCCESS:
            raise serializers.DjangoValidationError("Already Triggered")
        if not lead.leadpreview.text_extract:
            raise serializers.DjangoValidationError('Simplifed Text is empty')
        draft_entry_qs = DraftEntry.objects.filter(lead=lead, type=DraftEntry.Type.AUTO)
        if draft_entry_qs.exists():
            raise serializers.DjangoValidationError('Draft entry already exists')
        # Use already existing draft entry if found
        # Create new one and send trigger to deepl
        lead.auto_entry_extraction_status = Lead.AutoExtractionStatus.PENDING
        lead.save(update_fields=['auto_entry_extraction_status'])
        transaction.on_commit(
            lambda: trigger_request_for_auto_draft_entry_task.delay(lead.id)
        )
        return True

    def update(self, instance, validate_data):
        raise Exception("updated is not allowed")


class UpdateDraftEntrySerializer(
        DraftEntryBaseSerializer, ProjectPropertySerializerMixin, UserResourceSerializer, serializers.ModelSerializer
):
    class Meta:
        model = DraftEntry
        fields = (
            'lead',
            'is_discarded',
        )

    def create(self, _):
        raise Exception("Create is not Allowed")
