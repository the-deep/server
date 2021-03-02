from rest_framework import serializers

from deep.middleware import get_current_user
from user.serializers import EntryCommentUserSerializer
from entry.models import Entry
from project.models import ProjectMembership

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
    text = serializers.CharField(write_only=True)
    text_history = EntryReviewCommentTextSerializer(source='comment_texts', read_only=True, many=True)
    lead = serializers.IntegerField(source='entry.lead_id', read_only=True)
    created_by_detail = EntryCommentUserSerializer(source='created_by', read_only=True)
    mentioned_users_detail = EntryCommentUserSerializer(source='mentioned_users', read_only=True, many=True)
    comment_type_display = serializers.CharField(source='get_comment_type_display', read_only=True)

    class Meta:
        model = EntryReviewComment
        fields = '__all__'
        read_only_fields = ('entry', 'is_resolved', 'created_by', 'resolved_at')

    def _get_entity(self):
        if not hasattr(self, '_entry'):
            entry = Entry.objects.get(pk=int(self.context['entry_id']))
            self._entry = entry
        return self._entry

    def validate_comment_type(self, comment_type):
        if comment_type == CommentType.COMMENT:
            return comment_type  # No additional validation/action required

        entry = self._get_entity()
        current_user = get_current_user()
        approved_by_qs = Entry.approved_by.through.objects.filter(entry=entry, user=current_user)
        if comment_type == CommentType.APPROVE:
            if approved_by_qs.exists():
                raise serializers.ValidationError({'comment_type': 'Already approved'})
            entry.approved_by.add(current_user)
        elif comment_type == CommentType.UNAPPROVE:
            if not approved_by_qs.exists():
                raise serializers.ValidationError({'comment_type': 'Need to approve first'})
            entry.approved_by.remove(current_user)
        elif comment_type == CommentType.CONTROL:
            if entry.verified:
                raise serializers.ValidationError({'comment_type': 'Already verified/controlled'})
            entry.verify(current_user)
        elif comment_type == CommentType.UNCONTROL:
            if not entry.verified:
                raise serializers.ValidationError({'comment_type': 'Need to verified/controlled first'})
            entry.verify(current_user, verified=False)
        return comment_type

    def validate(self, data):
        mentioned_users = data.get('mentioned_users')
        data['entry'] = entry = self._get_entity()
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
        text_change = True
        if instance is None:  # Create
            instance = super().create(validated_data)
        else:  # Update
            text_change = instance.text != text
            instance = super().update(instance, validated_data)
            instance.save()
        if text and text_change:
            self._add_comment_text(instance, text)
        return instance

    def create(self, validated_data):
        return self.comment_save(validated_data)

    def update(self, instance, validated_data):
        return self.comment_save(validated_data, instance)


class ApprovedBySerializer(EntryCommentUserSerializer):
    pass
