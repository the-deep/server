import random
import re
import factory
import datetime
import subprocess
from factory import fuzzy
from django.core.management import BaseCommand
from django.conf import settings
from django.db import transaction
from organization.models import Organization
from project.factories import ProjectFactory
from project.models import Project, ProjectRole
from user.factories import UserFactory
from lead.factories import LeadFactory, LeadPreviewFactory
from lead.models import Lead, LeadPreview
from user.models import Feature, User
from analysis_framework.models import AnalysisFrameworkRole, AnalysisFramework
from analysis_framework.factories import (
    AnalysisFrameworkFactory,
    SectionFactory,
    WidgetFactory,
    AfFilterFactory,
    AnalysisFrameworkTagFactory
)
from entry.factories import (
    EntryFactory,
)

PROJECT_PREFIX = 'TC-Project-'
USER_PREFIX = 'TC-User-'
ANALYSIS_FRAMEWORK_PREFIX = 'TC-AF-'
DEFAULT_START_DATETIME = datetime.datetime(year=2017, month=1, day=1, tzinfo=datetime.timezone.utc)
created_at_fuzzy = fuzzy.FuzzyDateTime(DEFAULT_START_DATETIME)


class Command(BaseCommand):
    def handle(self, **kwargs):
        if not settings.ALLOW_DUMMY_DATA_GENERATION:
            self.stderr.write(
                'Dummy data generation is not allowed for this instance.'
                ' Use environment variable ALLOW_DUMMY_DATA_GENERATION to enable this'
            )
            return
        if not Organization.objects.all():
            subprocess.run(['python', 'manage.py', 'load_organizations'], check=True)
            self.stdout.write(self.style.SUCCESS('load_organizations command executed successfully!'))
        if not Feature.objects.all():
            subprocess.run(['python', 'manage.py', 'loaddata', 'features.json'], check=True)
            self.stdout.write(self.style.SUCCESS('features command executed successfully!'))
        if not AnalysisFrameworkRole.objects.all():
            subprocess.run(['python', 'manage.py', 'loaddata', 'features.json'], check=True)
            self.stdout.write(self.style.SUCCESS('AnalysisFrameworkRole command executed successfully!'))
        self.run()

    @staticmethod
    def _fuzzy_created_at(model, objects):
        """
        NOTE: This mutates the provided arguments
        It updates and save the created_at to database
        Django set's the created_at on first save, so we need to do this later manually
        """
        update_objs = []
        for obj in objects:
            obj.created_at = created_at_fuzzy.fuzz()
            update_objs.append(obj)
        model.objects.bulk_update(update_objs, ('created_at',))

    def generate_project(self, user: User, af: AnalysisFramework):
        # PROJECTS
        existing_project = Project.objects.filter(title__startswith=PROJECT_PREFIX).count()
        project = ProjectFactory.create(
            title=f'{PROJECT_PREFIX}{existing_project}',
            description=factory.Faker('text', max_nb_chars=400),
            analysis_framework=af
        )
        if not ProjectRole.objects.all():
            subprocess.run(['python', 'manage.py', 'loaddata', 'project_roles.json'], check=True)
            self.stdout.write(self.style.SUCCESS('project roles command executed successfully!'))
        project.add_member(user, role=ProjectRole.objects.get(type=ProjectRole.Type.ADMIN))
        project.created_by = user
        # Fuzzy out the created at
        project.save()
        return project

    def generate_analysis_framwework(self):
        existing_af = AnalysisFramework.objects.filter(title__startswith=ANALYSIS_FRAMEWORK_PREFIX).count()
        af = AnalysisFrameworkFactory.create(
            title=f'{ANALYSIS_FRAMEWORK_PREFIX}{existing_af}'
        )
        AnalysisFrameworkTagFactory.create_batch(4)
        section = SectionFactory.create_batch(
            2,
            analysis_framework_id=af.id,
            tooltip=factory.Faker('text', max_nb_chars=50)
        )
        [
            WidgetFactory.create(
                analysis_framework_id=af.id,
                section_id=section.id,
            )
            for section in section
        ]
        AfFilterFactory.create(
            analysis_framework_id=af.id
        )
        return af

    def get_random_sentence(self, text):
        # Split text into sentences using regex
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        # Select a random sentence
        random_sentence = random.choice(sentences)
        return random_sentence

    def generate_leads(self, project: Project, count: int):
        # Leads
        leads = LeadFactory.create_batch(
            count,
            project=project,
            is_assessment_lead=True,
        )
        # Previews
        # NOTE: Bulk create is throwing onetoone key already exists error
        [
            LeadPreviewFactory.create(lead=lead)
            for lead in leads
        ]
        # Fuzzy out the created at
        self._fuzzy_created_at(Lead, leads)
        return leads

    def generate_entry(self, lead: Lead, count):
        for lead in lead:
            data = LeadPreview.objects.get(lead=lead.id)
            excerpt = self.get_random_sentence(data.text_extract)
            EntryFactory.create_batch(
                count,
                excerpt=excerpt,
                lead=lead,
                dropped_excerpt=excerpt,
                image=None,
            )
        return

    @transaction.atomic
    def run(self):
        user = User.objects.filter(email__startswith=USER_PREFIX).count()
        email = f'{USER_PREFIX}{user}@gmail.com'
        user = UserFactory.create(email=email, is_staff=True, is_superuser=True)
        user_data = {}
        user_data['email'] = user.email
        user_data['password'] = user.password_text
        self.stderr.write(str(user_data))
        af = self.generate_analysis_framwework()
        project = self.generate_project(user, af)
        leads = self.generate_leads(project, 30)
        self.generate_entry(leads, 5)
        af.add_member(user)
        self.stderr.write(f'{af}')
        return user_data







