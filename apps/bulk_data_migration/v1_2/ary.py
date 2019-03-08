from ary.models import Assessment
from utils.common import random_key


def migrate_assessment(obj):
    methodology = obj.methodology
    attributes = methodology.get('attributes')
    if not attributes:
        return

    for attribute in attributes:
        if not attribute.get('key'):
            attribute['key'] = random_key()

    Assessment.objects.filter(id=obj.id)\
        .update(methodology=methodology)


def migrate_ary(**filters):
    for obj in Assessment.objects.filter(**filters):
        migrate_assessment(obj)
