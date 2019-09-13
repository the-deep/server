import traceback
import logging

from django.db import transaction
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from .forms import MergeForm

logger = logging.getLogger(__name__)


@transaction.atomic
def _merge_organizations(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    mergable_objects, count, perms_needed = modeladmin.get_merged_objects(queryset, request)

    if request.POST.get('post'):
        form = MergeForm(request.POST, organizations=queryset)
        if perms_needed:
            raise PermissionDenied
        n = queryset.count()
        if n:
            for obj in queryset:
                obj_display = str(obj)
                modeladmin.log_merge(request, obj, obj_display)
            parent_organization = form.data.get('parent_organization')
            modeladmin.merge_queryset(request, parent_organization, queryset)
            modeladmin.message_user(request, _("Successfully merged %(count)d %(items)s.") % {
                "count": n, "items": model_ngettext(modeladmin.opts, n)
            }, messages.SUCCESS)
        # Return None to display the change list page again.
        return None

    objects_name = model_ngettext(queryset)
    form = MergeForm(organizations=queryset)

    if perms_needed:
        title = _("Cannot merge organizations")
    else:
        title = _("Are you sure?")
    context = {
        **modeladmin.admin_site.each_context(request),
        'title': title,
        'objects_name': str(objects_name),
        'mergable_objects': mergable_objects,
        'model_count': count,
        'queryset': queryset,
        'perms_lacking': perms_needed,
        'opts': opts,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'media': modeladmin.media,
        'form': form,
        'adminform': helpers.AdminForm(
            form,
            list([(None, {'fields': form.base_fields})]),
            {},
        )
    }
    return TemplateResponse(request, 'organization/merge_confirmation.html', context)


def merge_organizations(modeladmin, request, queryset):
    try:
        return _merge_organizations(modeladmin, request, queryset)
    except Exception:
        logger.error('Error occured while merging organization', exc_info=True)
        messages.add_message(
            request, messages.ERROR,
            mark_safe(
                'Error occured while merging organization: <br><hr><pre>' + traceback.format_exc() + '</pre>'
            )
        )


merge_organizations.short_description = 'Merge Organizations'
merge_organizations.allowed_permissions = ('merge',)
merge_organizations.long_description = 'Merge Organizations and reflect changes to other part of the deep'
