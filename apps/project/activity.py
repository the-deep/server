from reversion.models import Version
from project.models import AnalysisFramework, CategoryEditor
from utils.common import random_key
import json


def get_diff(v1, v2):
    p1 = json.loads(v1.serialized_data)[0].get('fields')
    p2 = json.loads(v2.serialized_data)[0].get('fields')

    diff = {}

    def calc_simple_diff(key):
        if p1.get(key) != p2.get(key):
            diff[key] = {
                'new': p1.get(key),
                'old': p2.get(key),
            }

    def calc_model_diff(key, model):
        id1 = p1.get(key)
        id2 = p2.get(key)
        if id1 == id2:
            return
        m1 = id1 and model.objects.filter(id=id1).first()
        m2 = id2 and model.objects.filter(id=id2).first()
        diff[key] = {
            'new': m1 and {'id': m1.id, 'title': m1.title},
            'old': m2 and {'id': m2.id, 'title': m2.title},
        }

    calc_simple_diff('title')
    calc_simple_diff('description')
    calc_simple_diff('start_date')
    calc_simple_diff('end_date')
    calc_model_diff('analysis_framework', AnalysisFramework)
    calc_model_diff('category_editor', CategoryEditor)

    if len(diff.keys()) > 0:
        return {
            'key': random_key(),
            'fields': diff,
            'user': {
                'name': v1.revision.user.profile.get_display_name(),
                'id': v1.revision.user.id,
            } if v1.revision.user else None,  # TODO: this is just a fix
            'timestamp': v1.revision.date_created,
        }
    return None


def project_activity_log(project):
    versions = Version.objects.get_for_object(project)[:10]
    for v1, v2 in zip(versions, versions[1:]):
        diff = get_diff(v1, v2)
        if diff:
            yield diff
