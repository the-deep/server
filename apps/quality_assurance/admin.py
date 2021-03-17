from django.contrib import admin

from .models import EntryReviewComment, EntryReviewCommentText


class EntryReviewCommentTextInline(admin.StackedInline):
    model = EntryReviewCommentText
    extra = 0


@admin.register(EntryReviewComment)
class EntryReviewCommentAdmin(admin.ModelAdmin):
    inlines = [EntryReviewCommentTextInline]
    autocomplete_fields = (
        'created_by', 'mentioned_users', 'entry'
    )
