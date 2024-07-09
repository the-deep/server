from promise import Promise
from collections import defaultdict

from django.utils.functional import cached_property
from django.db import models

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from entry.models import Entry
from organization.models import Organization

from organization.dataloaders import OrganizationLoader

from .models import Lead, LeadPreview, LeadGroup, LeadPreviewAttachment
from assisted_tagging.models import DraftEntry
from assessment_registry.models import AssessmentRegistry


class LeadPreviewLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        lead_preview_qs = LeadPreview.objects.filter(lead__in=keys)
        _map = {
            lead_preview.lead_id: lead_preview
            for lead_preview in lead_preview_qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class LeadPreviewAttachmentLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        lead_preview_attachment_qs = LeadPreviewAttachment.objects.filter(lead__in=keys)
        lead_preview_attachments = defaultdict(list)
        for lead_preview_attachment in lead_preview_attachment_qs:
            lead_preview_attachments[lead_preview_attachment.lead_id].append(lead_preview_attachment)
        return Promise.resolve([lead_preview_attachments.get(key) for key in keys])


class EntriesCountLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        active_af = self.context.active_project.analysis_framework
        stat_qs = Entry.objects\
            .filter(lead__in=keys)\
            .order_by('lead').values('lead')\
            .annotate(
                total=models.functions.Coalesce(
                    models.Count(
                        'id',
                        filter=models.Q(analysis_framework=active_af)
                    ),
                    0,
                ),
                controlled=models.functions.Coalesce(
                    models.Count(
                        'id',
                        filter=models.Q(controlled=True, analysis_framework=active_af)
                    ),
                    0,
                ),
            ).values('lead_id', 'total', 'controlled')
        _map = {
            stat.pop('lead_id'): stat
            for stat in stat_qs
        }
        _dummy = {
            'total': 0,
            'controlled': 0,
        }
        return Promise.resolve([_map.get(key, _dummy) for key in keys])


class LeadGroupLeadCountLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        lead_group_qs = LeadGroup.objects.filter(id__in=keys).annotate(
            lead_counts=models.Count('lead', distinct=True)
        )
        _map = {
            id: count
            for id, count in lead_group_qs.values_list('id', 'lead_counts')
        }
        return Promise.resolve([_map.get(key, 0) for key in keys])


class LeadAuthorsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        lead_author_qs = Lead.objects\
            .filter(id__in=keys, authors__isnull=False)\
            .values_list('id', 'authors__id')
        lead_author_map = defaultdict(list)
        organizations_id = set()
        for lead_id, author_id in lead_author_qs:
            lead_author_map[lead_id].append(author_id)
            organizations_id.add(author_id)

        organization_qs = Organization.objects.filter(id__in=organizations_id)
        _map = {
            org.id: org for org in organization_qs
        }
        return Promise.resolve([
            [
                _map.get(author)
                for author in lead_author_map.get(key, [])
            ]
            for key in keys
        ])


class LeadAssessmentIdLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        assessments_qs = AssessmentRegistry.objects.filter(lead__in=keys).values_list('id', 'lead')
        _map = {
            lead_id: _id for _id, lead_id in assessments_qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class LeadDraftEntryCountLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        stat_qs = DraftEntry.objects\
            .filter(lead__in=keys)\
            .order_by('lead').values('lead')\
            .annotate(
                discarded_draft_entry=models.functions.Coalesce(
                    models.Count(
                        'id',
                        filter=models.Q(is_discarded=True)
                    ),
                    0,
                ),
                undiscarded_draft_entry=models.functions.Coalesce(
                    models.Count(
                        'id',
                        filter=models.Q(is_discarded=False)
                    ),
                    0,
                ),
            ).values('lead_id', 'undiscarded_draft_entry', 'discarded_draft_entry')
        _map = {
            stat.pop('lead_id'): stat
            for stat in stat_qs
        }
        return Promise.resolve([_map.get(key, _map) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def lead_preview(self):
        return LeadPreviewLoader(context=self.context)

    @cached_property
    def lead_preview_attachment(self):
        return LeadPreviewAttachmentLoader(context=self.context)

    @cached_property
    def entries_count(self):
        return EntriesCountLoader(context=self.context)

    @cached_property
    def leadgroup_lead_counts(self):
        return LeadGroupLeadCountLoader(context=self.context)

    @cached_property
    def source_organization(self):
        return OrganizationLoader(context=self.context)

    @cached_property
    def author_organizations(self):
        return LeadAuthorsLoader(context=self.context)

    @cached_property
    def assessment_id(self):
        return LeadAssessmentIdLoader(context=self.context)

    @cached_property
    def draftentry_count(self):
        return LeadDraftEntryCountLoader(context=self.context)
