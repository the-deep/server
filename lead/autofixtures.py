from django.contrib.auth.models import User

from autofixture import register, generators, AutoFixture
from urllib.parse import urlparse

from .models import Lead

import random


class LeadAutoFixture(AutoFixture):
    overwrite_defaults = True
    field_values = {
        'text': '',
        'url': '',
        'website': '',
        'attachment': None,
    }

    def post_process_instance(self, instance, commit):
        choice = random.randint(1, 2)
        if choice == 1:
            instance.text = generators.LoremGenerator().generate()
        else:
            instance.url = generators.URLGenerator().generate()
            instance.website = urlparse(instance.url).netloc
        instance.save()


register(Lead, LeadAutoFixture)


# Since autofixture is quite slow, create a method to use to generate
# large number of leads more efficiently
def create_many_leads(num, created_by, project):
    leads = []
    for i in range(num):
        lead = Lead()
        lead.title = generators.LoremGenerator(max_length=20).generate()
        lead.project = project
        lead.created_by = created_by
        lead.modified_by = created_by
        lead.status = random.choice(['pending', 'processed'])
        lead.condidentiality = random.choice([
            'unprotected',
            'protected',
            'restricted',
            'confidential',
        ])
        lead.published_on = generators.DateGenerator().generate()
        leads.append(lead)

    Lead.objects.bulk_create(leads)

    LeadAssigneeThrough = Lead.assignee.through
    assignee_throughs = []

    all_users = list(User.objects.all())
    count = len(all_users)
    for lead in leads:
        assignee_throughs.append(
            LeadAssigneeThrough(
                lead_id=lead.id,
                user_id=all_users[random.randint(0, count - 1)].id,
            )
        )

    LeadAssigneeThrough.objects.bulk_create(assignee_throughs)
