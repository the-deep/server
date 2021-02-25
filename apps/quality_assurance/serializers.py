from rest_framework import serializers

from user.serializers import EntryCommentUserSerializer
from entry.models import Entry
from project.models import ProjectMembership

from .models import (
    EntryReviewComment,
    EntryReviewCommentText,
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

    def _get_entry(self):
        if not hasattr(self, '_entry'):
            entry = Entry.objects.get(pk=int(self.context['entry_id']))
            self._entry = entry
        return self._entry

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
        data['created_by'] = self.context['request'].user
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
