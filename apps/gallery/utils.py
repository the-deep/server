from django.conf import settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from gallery.enums import PrivateFileModuleType
from deep.permissions import ProjectPermissions as PP
from lead.models import Lead


def get_private_file_url(private_file_module_type: PrivateFileModuleType, id: int, filename: str):
    return '{protocol}://{domain}{url}'.format(
        protocol=settings.HTTP_PROTOCOL,
        domain=settings.DJANGO_API_HOST,
        url=reverse(
            'external_private_url',
            kwargs={
                'module': private_file_module_type.value,
                'identifier': urlsafe_base64_encode(force_bytes(id)),
                'filename': filename
            }
        )
    )


def check_private_condifential_level_permission(user, project, level):
    permission = PP.get_permissions(project, user)
    if PP.Permission.VIEW_ENTRY in permission:
        if PP.Permission.VIEW_ALL_LEAD in permission:
            return True
        elif PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD in permission:
            return level == Lead.Confidentiality.UNPROTECTED
    return False
