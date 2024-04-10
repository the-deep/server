from django.utils.functional import cached_property

from promise import Promise

from entry.models import Entry
from notification.models import Assignment
from lead.models import Lead

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin


class AssignmentLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        assignment_qs = list(
            Assignment.objects
            .filter(id__in=keys)
            .values_list('id', 'content_type__app_label', 'object_id')
        )

        leads_id = []
        entries_id = []
        for _, content_type, object_id in assignment_qs:
            if content_type == 'entry':
                entries_id.append(object_id)
            elif content_type == 'lead':
                leads_id.append(object_id)

        lead_id_map = {
            lead.id: lead
            for lead in Lead.objects.filter(id__in=leads_id)
        } if leads_id else {}

        entry_id_map = {
            entry.id: entry
            for entry in Entry.objects.filter(id__in=entries_id)
        } if entries_id else {}

        _result = {
            _id: {
                'content_type': content_type,
                'lead': lead_id_map.get(object_id) if content_type == 'lead' else None,
                'entry': entry_id_map.get(object_id) if content_type == 'entry' else None,
            }
            for _id, content_type, object_id in assignment_qs
        }
        return Promise.resolve([_result[key] for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def assignment(self):
        return AssignmentLoader(context=self.context)
