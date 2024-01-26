import random
import datetime
import typing

from factory import fuzzy
from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.conf import settings

from user.models import User
from ary.models import AssessmentTemplate
from lead.models import Lead
from project.models import Project, ProjectRole
from geo.models import Region, GeoArea
from organization.models import Organization
from assessment_registry.models import (
    AssessmentRegistryOrganization,
    Question,
    SummaryIssue,
)
from project.factories import ProjectFactory
from lead.factories import LeadFactory, LeadPreviewFactory
from assessment_registry.factories import (
    AssessmentRegistryFactory,
    MethodologyAttributeFactory,
    AdditionalDocumentFactory,
    ScoreRatingFactory,
    ScoreAnalyticalDensityFactory,
    AnswerFactory,
    SummaryMetaFactory,
    SummarySubPillarIssueFactory,
    SummaryFocusFactory,
    SummarySubDimensionIssueFactory,
)


DUMMY_PROJECT_PREFIX = 'Dummy Project (Assessment)'
DEFAULT_START_DATETIME = datetime.datetime(year=2017, month=1, day=1, tzinfo=datetime.timezone.utc)
created_at_fuzzy = fuzzy.FuzzyDateTime(DEFAULT_START_DATETIME)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--delete-existing', dest='delete_existing', action='store_true')
        parser.add_argument('--regions-from-project', dest='project_for_regions')
        parser.add_argument('--user-email', dest='user_email', required=True)
        parser.add_argument('--leads-counts', dest='leads_count', type=int, default=50)

    def handle(self, **kwargs):
        if not settings.ALLOW_DUMMY_DATA_GENERATION:
            self.stderr.write(
                'Dummy data generation is not allowed for this instance.'
                ' Use environment variable ALLOW_DUMMY_DATA_GENERATION to enable this'
            )
            return
        user_email = kwargs['user_email']
        leads_count = kwargs['leads_count']
        delete_existing = kwargs['delete_existing']
        project_for_regions = kwargs['project_for_regions']
        user = User.objects.get(email=user_email)
        self.ur_args = {
            'created_by': user,
            'modified_by': user,
        }
        self.run(user, leads_count, delete_existing, project_for_regions)

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

    def generate_leads(self, project: Project, count: int):
        # Leads
        leads = LeadFactory.create_batch(
            count,
            project=project,
            is_assessment_lead=True,
            **self.ur_args,
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

    def generate_assessments(self, project: Project, leads: typing.List[Lead]):
        # Organization data
        assessment_organization_types = [c[0] for c in AssessmentRegistryOrganization.Type.choices]
        organizations = list(
            Organization.objects.only('id')[:300]
        )
        organizations_len = len(organizations)
        # Geo data
        regions = list(
            Region.objects.filter(
                project=project,
            ).only('id')
        )
        geo_areas = list(
            GeoArea.objects.filter(
                admin_level__region__project=project,
                admin_level__level__in=[1, 2],
            ).annotate(
                region_id=models.F('admin_level__region'),
            ).only('id')
        )
        regions_len = len(regions)
        # Assessment Questions
        ary_questions = list(Question.objects.only('id').all()[:200])
        ary_questions_len = len(ary_questions)
        # Issues
        summary_issues = list(SummaryIssue.objects.only('id').all()[:100])

        # Assessments
        total_leads = len(leads)
        for index, lead in enumerate(leads, start=1):
            self.stdout.write(f'Processing for lead ({index}/{total_leads}): {lead}')
            assessment_registry = AssessmentRegistryFactory.create(
                project=project,
                lead=lead,
                **self.ur_args,
            )
            assessment_registry.created_at = fuzzy.FuzzyDateTime(lead.created_at).fuzz()
            assessment_registry.save(update_fields=('created_at',))
            if organizations:
                _organizations = random.sample(
                    organizations,
                    random.randint(0, organizations_len)
                )
                stakeholders = []
                for assessment_organization_type, organization in zip(
                    assessment_organization_types,
                    _organizations,
                ):
                    stakeholders.append(
                        AssessmentRegistryOrganization(
                            organization_type=assessment_organization_type,
                            organization=organization,
                            assessment_registry=assessment_registry,
                        )
                    )
                AssessmentRegistryOrganization.objects.bulk_create(stakeholders)
                del _organizations
                del stakeholders

            if regions:
                selected_regions = list(
                    random.sample(
                        regions,
                        random.randint(1, min(regions_len, 3)),
                    )
                )
                assessment_registry.bg_countries.add(*selected_regions)

                if geo_areas:
                    geo_areas_filtered = [
                        geo_area
                        for geo_area in geo_areas
                        # Annotated field region_id
                        if geo_area.region_id in [  # pyright: ignore [reportGeneralTypeIssues]
                            region.id
                            for region in selected_regions
                        ]
                    ]
                    assessment_registry.locations.add(
                        *random.sample(
                            geo_areas_filtered,
                            random.randint(
                                1,
                                min(len(geo_areas_filtered), 20),
                            ),
                        )
                    )
                    del geo_areas_filtered
                del selected_regions

            ary_params = {'assessment_registry': assessment_registry}

            AdditionalDocumentFactory.create_batch(random.randint(0, 10), **ary_params)
            MethodologyAttributeFactory.create_batch(random.randint(0, 10), **ary_params)
            ScoreRatingFactory.create_batch(random.randint(0, 40), **ary_params)
            ScoreAnalyticalDensityFactory.create_batch(random.randint(0, 40), **ary_params)

            # Questions
            for question_ in random.sample(ary_questions, random.randint(0, ary_questions_len)):
                # NOTE: With BulkCreate unique error is thrown
                AnswerFactory.create(
                    question=question_,
                    **ary_params
                )
            # Summary
            SummaryMetaFactory.create(**ary_params)
            if summary_issues:
                for _ in range(random.randint(0, 100)):
                    SummarySubPillarIssueFactory.create(
                        summary_issue=random.choice(summary_issues),
                        **ary_params,
                    )
                    SummarySubDimensionIssueFactory.create(
                        summary_issue=random.choice(summary_issues),
                        **ary_params,
                    )
            SummaryFocusFactory.create_batch(random.randint(1, 40), **ary_params)

    @transaction.atomic
    def run(self, user: User, leads_count: int, delete_existing: bool, project_for_regions: typing.Union[int, None]):
        existing_dummy_projects = Project.objects.filter(title__startswith=DUMMY_PROJECT_PREFIX)
        existing_dummy_projects_count = existing_dummy_projects.count()
        if delete_existing:
            if existing_dummy_projects_count:
                self.stdout.write(f'There are {existing_dummy_projects_count} existing dummy projects.')
                for _id, title, creator in existing_dummy_projects.values_list('id', 'title', 'created_by__email'):
                    self.stdout.write(f'{_id}: {title} - {creator}')
                result = input("%s " % "This will delete above projects. Are you sure? type YES to delete: ")
                if result == 'YES':
                    with transaction.atomic():
                        Project.objects.filter(
                            pk__in=existing_dummy_projects.values('id')
                        ).delete()
                    existing_dummy_projects_count = 0

        project = ProjectFactory.create(
            title=f'{DUMMY_PROJECT_PREFIX} {existing_dummy_projects_count}',
            assessment_template=AssessmentTemplate.objects.first(),
            **self.ur_args,
        )
        project.created_at = DEFAULT_START_DATETIME
        project.save(update_fields=('created_at',))
        if project_for_regions is None:
            # Using top used regions
            project_regions = list(
                Region.objects.filter(
                    is_published=True,
                ).annotate(
                    project_count=models.Count('project'),
                ).order_by('-project_count').only('id')[:5]
            )
        else:
            # Using regions from provided project
            project_regions = list(
                Region.objects.filter(
                    is_published=True,
                    project=project_for_regions,
                ).distinct().only('id')
            )
            assert len(project_regions) > 0, 'There are no regions in selected project'

        project.regions.add(*project_regions)
        project.add_member(user, role=ProjectRole.objects.get(type=ProjectRole.Type.ADMIN))
        self.stdout.write(f'Generating assessments for new project: <pk: {project.pk}>{project.title}')
        # Leads
        self.stdout.write(f'Generating {leads_count} leads')
        leads = self.generate_leads(project, leads_count)
        # Assessments
        self.stdout.write(f'Generating assessments for {leads_count} leads')
        self.generate_assessments(project, leads)
