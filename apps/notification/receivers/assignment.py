from django.dispatch import receiver
from django.db.models.signals import (
    m2m_changed,
    post_delete,
)

from deep.middleware import get_current_user
from lead.models import Lead
from notification.models import Assignment
from entry.models import EntryComment


@receiver(m2m_changed, sender=Lead.assignee.through)
def lead_assignment_signal(sender, instance, action, **kwargs):
    pk_set = kwargs.get('pk_set', [])
    # Gets the username from the request with a middleware helper
    user = get_current_user()
    if action == 'post_add' and pk_set and user:
        for receiver_user in pk_set:
            if Assignment.objects.filter(lead__id=instance.id,
                                         created_for_id=receiver_user,
                                         project=instance.project).exists():
                continue
            Assignment.objects.create(
                content_object=instance,
                created_for_id=receiver_user,
                project=instance.project,
                created_by=user,)

    elif action == 'post_remove' and pk_set and user:
        for receiver_user in pk_set:
            Assignment.objects.filter(
                lead__id=instance.id,
                created_for_id=receiver_user,
            ).delete()

    # handling `post_clear` since single assignee is passed
    # though the api
    elif action == 'post_clear':
        Assignment.objects.filter(lead__id=instance.id).delete()


@receiver(m2m_changed, sender=EntryComment.assignees.through)
def entrycomment_assignment_signal(sender, instance, action, **kwargs):
    pk_set = kwargs.get('pk_set', [])
    # Gets the username from the request with a middleware helper
    user = get_current_user()
    if action == 'post_add' and pk_set and user:
        for receiver_user in pk_set:
            if Assignment.objects.filter(entry_comment__id=instance.id,
                                         created_for_id=receiver_user,
                                         project=instance.entry.project).exists():
                continue
            Assignment.objects.create(
                content_object=instance,
                created_for_id=receiver_user,
                project=instance.entry.project,
                created_by=user,
            )

    elif action == 'post_remove' and pk_set and user:
        for receiver_user in pk_set:
            Assignment.objects.filter(
                entry_comment__id=instance.id,
                created_for_id=receiver_user,
            ).delete()


@receiver(post_delete, sender=Lead)
@receiver(post_delete, sender=EntryComment)
def delete_related_assignment(sender, instance, *args, **kwargs):
    pk = instance.id
    if type(instance) == Lead:
        Assignment.objects.filter(lead__id=pk).delete()
    elif type(instance) == EntryComment:
        Assignment.objects.filter(entry_comment__id=pk).delete()
