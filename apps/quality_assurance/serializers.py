from django.db import transaction
from rest_framework import serializers

from deep.middleware import get_current_user
from user.serializers import EntryCommentUserSerializer, UserNotificationSerializer
from project.serializers import ProjectNotificationSerializer

from entry.models import Entry
from project.models import ProjectMembership
from notification.models import Notification
from notification.tasks import send_notifications_for_commit

from .models import (
    EntryReviewComment,
    EntryReviewCommentText,
    CommentType,
)


class EntryReviewCommentTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryReviewCommentText
        exclude = ('id', 'comment')


class EntryReviewCommentSerializer(serializers.ModelSerializer):
    text = serializers.CharField(write_only=True, required=False)
    text_history = EntryReviewCommentTextSerializer(source='comment_texts', read_only=True, many=True)
    lead = serializers.IntegerField(source='entry.lead_id', read_only=True)
    created_by_details = EntryCommentUserSerializer(source='created_by', read_only=True)
    mentioned_users_details = EntryCommentUserSerializer(source='mentioned_users', read_only=True, many=True)
    comment_type_display = serializers.CharField(source='get_comment_type_display', read_only=True)

    class Meta:
        model = EntryReviewComment
        fields = '__all__'
        read_only_fields = ('entry', 'is_resolved', 'created_by', 'resolved_at')

    def _get_entry(self):
        if not hasattr(self, '_entry'):
            entry = Entry.objects.get(pk=int(self.context['entry_id']))
            self._entry = entry
        return self._entry

    def validate_comment_type(self, comment_type):
        if self.instance and self.instance.comment_type:  # No validation needed for edit
            return self.instance.comment_type

        if comment_type == CommentType.COMMENT:
            return comment_type  # No additional validation/action required

        entry = self._get_entry()
        current_user = get_current_user()
        verified_by_qs = Entry.verified_by.through.objects.filter(entry=entry, user=current_user)

        if (
            comment_type in [CommentType.CONTROL, CommentType.UNCONTROL] and
            # TODO: Make sure this works for linked_group as well
            not ProjectMembership.objects.filter(
                project=entry.project,
                member=self.context['request'].user,
                badges__contains=[ProjectMembership.BadgeType.QA],
            ).exists()
        ):
            raise serializers.ValidationError({
                'comment_type': 'Controlled/UnControlled comment are only allowd by QA',
            })

        if comment_type == CommentType.VERIFY:
            if verified_by_qs.exists():
                raise serializers.ValidationError({'comment_type': 'Already verified'})
            entry.verified_by.add(current_user)
        elif comment_type == CommentType.UNVERIFY:
            if not verified_by_qs.exists():
                raise serializers.ValidationError({'comment_type': 'Need to be verified first'})
            entry.verified_by.remove(current_user)
        elif comment_type == CommentType.CONTROL:
            if entry.controlled:
                raise serializers.ValidationError({'comment_type': 'Already controlled'})
            entry.control(current_user)
        elif comment_type == CommentType.UNCONTROL:
            if not entry.controlled:
                raise serializers.ValidationError({'comment_type': 'Need to be controlled first'})
            entry.control(current_user, controlled=False)
        return comment_type

    def validate(self, data):
        mentioned_users = data.get('mentioned_users')
        data['entry'] = entry = self._get_entry()
        # Check if all assignes are members
        if mentioned_users:
            selected_existing_members_count = (
                ProjectMembership.objects.filter(project=entry.project, member__in=mentioned_users)
                .distinct('member').count()
            )
            if selected_existing_members_count != len(mentioned_users):
                raise serializers.ValidationError(
                    {'mentioned_users': "Selected mentioned users don't belong to this project"}
                )
        data['created_by'] = get_current_user()
        return data

    def _add_comment_text(self, comment, text):
        return EntryReviewCommentText.objects.create(
            comment=comment,
            text=text,
        )

    def comment_save(self, validated_data, instance=None):
        """
        Comment Middleware save logic
        """
        text = validated_data.pop('text', '').strip()
        comment_type = validated_data.get('comment_type', CommentType.__default__)
        # Make sure to check text required
        if not text and comment_type in [CommentType.COMMENT, CommentType.UNVERIFY, CommentType.UNCONTROL]:
            raise serializers.ValidationError({'text': 'Text is required'})

        current_text = instance and instance.text
        text_changed = current_text != text
        notify_meta = {'text_changed': text_changed}

        if instance is None:  # Create
            notify_meta['notification_type'] = Notification.ENTRY_REVIEW_COMMENT_ADD
            notify_meta['text_changed'] = True
            instance = super().create(validated_data)
        else:  # Update
            notify_meta['notification_type'] = Notification.ENTRY_REVIEW_COMMENT_MODIFY
            current_mentioned_users_pk = list(instance.mentioned_users.values_list('pk', flat=True))
            notify_meta['new_mentioned_users'] = [
                user
                for user in validated_data.get('mentioned_users', [])
                if user.pk not in current_mentioned_users_pk
            ]
            instance = super().update(instance, validated_data)
            instance.save()

        if text and text_changed:
            self._add_comment_text(instance, text)
        transaction.on_commit(
            lambda: send_notifications_for_commit(instance.pk, notify_meta)
        )
        return instance

    def create(self, validated_data):
        return self.comment_save(validated_data)

    def update(self, instance, validated_data):
        return self.comment_save(validated_data, instance)


class EntryReviewCommentNotificationSerializer(serializers.ModelSerializer):
    text = serializers.CharField(read_only=True)
    lead = serializers.IntegerField(source='entry.lead_id', read_only=True)
    project_details = ProjectNotificationSerializer(source='entry.project', read_only=True)
    created_by_details = UserNotificationSerializer(source='created_by', read_only=True)
    comment_type_display = serializers.CharField(source='get_comment_type_display', read_only=True)

    class Meta:
        model = EntryReviewComment
        fields = (
            'id', 'entry', 'created_at',
            'text', 'lead', 'project_details', 'created_by_details',
            'comment_type', 'comment_type_display',
        )


class VerifiedBySerializer(EntryCommentUserSerializer):
    pass
