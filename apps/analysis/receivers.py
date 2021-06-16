from typing import Counter
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from analysis.models import AnalyticalStatement


@receiver(pre_save, sender=AnalyticalStatement)
def model_version_signal(sender, instance, **kwargs):
    try:
        instance._pre_save_instance = AnalyticalStatement.objects.get(id=instance.id)
    except AnalyticalStatement.DoesNotExist:
        instance._pre_save_instance = instance

@receiver(post_save, sender=AnalyticalStatement)
def model_post_save(sender, instance, created, **kwargs):
    pre_save_instance = instance._pre_save_instance
    post_save_instance = instance

    if pre_save_instance.statement != post_save_instance.statement or\
        pre_save_instance.client_id != post_save_instance.client_id or \
        pre_save_instance.entries != post_save_instance.entries or \
        pre_save_instance.analysis_pillar != post_save_instance.analysis_pillar or \
        pre_save_instance.include_in_report != post_save_instance.include_in_report or \
        pre_save_instance.order != post_save_instance.order or \
        pre_save_instance.created_by != post_save_instance.created_by or \
        pre_save_instance.modified_by != post_save_instance.modified_by:

        post_save_instance.version += 1
        post_save_instance.save()
        post_save_instance.analysis_pillar.version += 1
        post_save_instance.analysis_pillar.save()