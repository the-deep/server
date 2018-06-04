from deep_migration.utils import (
    MigrationCommand,
    get_source_url,
    request_with_auth,
    get_migrated_gallery_file,
)

from deep_migration.models import (
    LeadMigration,
    ProjectMigration,
    UserMigration,
)
from lead.models import Lead

from django.utils.dateparse import parse_date
import reversion


def get_user(old_user_id):
    migration = UserMigration.objects.filter(old_id=old_user_id).first()
    return migration and migration.user


def get_project(project_id):
    migration = ProjectMigration.objects.filter(old_id=project_id).first()
    return migration and migration.project


CONFIDENTIALITY_MAP = {
    'UNP': Lead.UNPROTECTED,
    'PRO': Lead.PROTECTED,
    'RES': Lead.RESTRICTED,
    'CON': Lead.CONFIDENTIAL,
}

STATUS_MAP = {
    'PEN': Lead.PENDING,
    'PRO': Lead.PROTECTED,
}


class Command(MigrationCommand):
    def run(self):
        data = request_with_auth(get_source_url('leads'))

        if not data or not data.get('data'):
            print('Couldn\'t find leads data')

        leads = data['data']
        with reversion.create_revision():
            for lead in leads:
                self.import_lead(lead)

    def import_lead(self, data):
        print('------------')
        print('Migrating lead')

        old_id = data['id']
        title = data['name']
        project_id = data['event']
        project = get_project(project_id)

        if not project:
            print('Project with old id: {} doesn\'t exist'.format(project_id))
            return None

        print('{} - {}'.format(old_id, title))

        migration, _ = LeadMigration.objects.get_or_create(
            old_id=old_id,
        )
        if not migration.lead:
            lead = Lead.objects.create(
                title=title,
                project=project,
            )
            migration.lead = lead
            migration.save()

        lead = migration.lead
        lead.title = title
        lead.source = data['source'] or ''
        lead.confidentiality = CONFIDENTIALITY_MAP[data['confidentiality']]
        lead.status = STATUS_MAP[data['status']]

        lead.published_on = data['published_at'] and \
            parse_date(data['published_at'])
        lead.created_by = get_user(data['created_by'])
        lead.modified_by = lead.created_by

        if data.get('description'):
            lead.source_type = Lead.TEXT
            lead.text = data['description']

        elif data.get('url'):
            lead.source_type = Lead.WEBSITE
            lead.website = data['website']
            lead.url = data['url']

        elif data.get('attachment'):
            lead.source_type = Lead.DISK
            lead.attachment = get_migrated_gallery_file(
                data['attachment']['url']
            )

        lead.save()

        if data.get('assignee'):
            lead.assignee.add(get_user(data.get('assignee')))

        Lead.objects.filter(id=lead.id).update(created_at=data['created_at'])

        return lead
