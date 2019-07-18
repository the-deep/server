from django.core.management.base import BaseCommand

from analysis_framework.models import (
    AnalysisFramework as AF,
    AnalysisFrameworkRole as AFRole,
    AnalysisFrameworkMembership as AFMembership,
)


class Command(BaseCommand):
    help = 'Add framework owner membership for all creators of frameworks'

    def handle(self, *args, **options):
        add_owner_memberships_to_existing_frameworks()


def add_owner_memberships_to_existing_frameworks():
    priv_role = AFRole.objects.get(
        can_add_user=True,
        is_private_role=True,
        can_clone_framework=False,
        can_edit_framework=True,
        can_use_in_other_projects=True
    )

    pub_role = AFRole.objects.get(
        can_add_user=True,
        is_private_role=False,
        can_clone_framework=True,
        can_edit_framework=True,
        can_use_in_other_projects=True
    )

    for af in AF.objects.all():
        if not AFMembership.objects.filter(framework=af, member=af.created_by).exists():
            # Means creator's membership does not exist, So create one
            owner_role = priv_role if af.is_private else pub_role
            AFMembership.objects.create(
                framework=af,
                member=af.created_by,
                joined_at=af.created_at,
                role=owner_role
            )
