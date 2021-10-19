from django.db import models
from django.utils.functional import cached_property

from entry.models import Entry
from user.models import User


# ---------------------------------------------- Abstract Table ---------------------------------------
class BaseReviewComment(models.Model):
    created_by = models.ForeignKey(User, related_name='%(class)s_created', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    mentioned_users = models.ManyToManyField(User, blank=True)

    class Meta:
        abstract = True
        ordering = ('-id',)

    def can_delete(self, user):
        return self.can_modify(user)

    def can_modify(self, user):
        return self.created_by == user

    @classmethod
    def get_for(cls, user):
        return (
            cls.objects.select_related(
                'entry',
                'created_by',
                'created_by__profile',
                'created_by__profile__display_picture',
            ).prefetch_related(
                'comment_texts',
                'mentioned_users',
                'mentioned_users__profile',
                'mentioned_users__profile__display_picture',
            ).filter(
                models.Q(entry__lead__project__members=user) |
                models.Q(entry__lead__project__user_groups__members=user)
            ).distinct()
        )

    @cached_property
    def text(self):
        last_comment_text = self.comment_texts.order_by('-id').first()
        if last_comment_text:
            return last_comment_text.text


class BaseReviewCommentText(models.Model):
    """
    NOTE: Define comment
        comment = models.ForeignKey(BaseReviewComment, related_name='comment_texts', on_delete=models.CASCADE)
    """
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()

    class Meta:
        abstract = True
        ordering = ('-id',)


# ---------------------------------------------- Non-Abstract Table -------------------------------------

class EntryReviewComment(BaseReviewComment):
    class CommentType(models.IntegerChoices):
        COMMENT = 0, 'Comment'
        VERIFY = 1, 'Verify'
        UNVERIFY = 2, 'Unverify'
        CONTROL = 3, 'Control'
        UNCONTROL = 4, 'UnControl'

    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    comment_type = models.IntegerField(choices=CommentType.choices, default=CommentType.COMMENT)

    class Meta(BaseReviewComment.Meta):
        abstract = False

    def __str__(self):
        return f'{self.entry}: {self.text}'

    def get_related_users(self, skip_owner_user=True):
        users = list(
            self.mentioned_users.through.objects
            .filter(entryreviewcomment__entry=self.entry)
            .values_list('user', flat=True).distinct()
        )
        users.extend(
            type(self).objects
            .filter(entry=self.entry)
            .values_list('created_by_id', flat=True).distinct()
        )
        queryset = User.objects.filter(pk__in=set(users))
        if skip_owner_user:
            queryset = queryset.exclude(pk=self.created_by_id)
        return queryset


class EntryReviewCommentText(BaseReviewCommentText):
    comment = models.ForeignKey(
        EntryReviewComment, related_name='comment_texts', on_delete=models.CASCADE
    )

    class Meta(BaseReviewCommentText.Meta):
        abstract = False
