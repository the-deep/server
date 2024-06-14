from django.contrib import admin

from .models import EntryReviewComment, EntryReviewCommentText


class EntryReviewCommentTextInline(admin.StackedInline):
    model = EntryReviewCommentText
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(EntryReviewComment)
class EntryReviewCommentAdmin(admin.ModelAdmin):
    inlines = [EntryReviewCommentTextInline]
    list_display = ("id", "created_by", "created_at")
    readonly_fields = (
        "created_at",
        "entry_comment",
    )
    autocomplete_fields = ("created_by", "mentioned_users", "entry")
