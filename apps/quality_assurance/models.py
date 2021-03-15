from django.db import models
from django_enumfield import enum

from entry.models import Entry
from user.models import User


# ---------------------------------------------- Abstract Table ---------------------------------------
class CommentType(enum.Enum):
    COMMENT = 0
    APPROVE = 1
    UNAPPROVE = 2
    CONTROL = 3
    UNCONTROL = 4

    __default__ = COMMENT
    __labels__ = {
        COMMENT: 'Comment',
        APPROVE: 'Approve',
        UNAPPROVE: 'Unapprove',
        CONTROL: 'Control',
        UNCONTROL: 'UnControl',
    }


class BaseReviewComment(models.Model):
    created_by = models.ForeignKey(User, related_name='%(class)s_created', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    comment_type = enum.EnumField(CommentType)
    mentioned_users = models.ManyToManyField(User, blank=True)

    class Meta:
        abstract = True
        ordering = ('-id',)

    def __str__(self):
        return f'{self.entry}: {self.text}'

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

    @property
    def text(self):
        return self.comment_texts.last()


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
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)

    class Meta(BaseReviewComment.Meta):
        abstract = False

    def get_related_users(self, skip_owner_user=True):
        users = (
            self.mentioned_users.through.objects
            .filter(entryreviewcomment__entry=self)
            .values_list('id', flat=True).distinct()
        )
        users.extend(
            self.objects
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
