from django.db import models
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib import admin

from deep.admin import document_preview, linkify, ReadOnlyMixin

from .actions import merge_organizations
from .models import (
    OrganizationType,
    Organization,
)


@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_organization_count',)
    search_fields = ('title',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            organization_count=models.Count('organization')
        )

    def get_organization_count(self, instance):
        if instance:
            return instance.organization_count
    get_organization_count.short_description = 'Organization Count'


class OrganizationInline(ReadOnlyMixin, admin.TabularInline):
    model = Organization
    can_delete = False
    verbose_name_plural = 'Merged Organizations'
    extra = 0


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ('title', 'short_name', 'long_name')
    list_display = ('title', 'short_name', linkify('organization_type'),)
    readonly_fields = (document_preview('logo', 'Logo Preview'),)
    list_filter = ('organization_type', 'verified',)
    actions = (merge_organizations,)
    exclude = ('parent',)
    inlines = [OrganizationInline]
    autocomplete_fields = (
        'created_by', 'modified_by', 'logo',
        'organization_type', 'regions', 'parent',
    )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['has_merge_permission'] = self.has_merge_permission(request)
        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)

    def has_merge_permission(self, request):
        return request.user.has_perm('organization.can_merge')

    def merge_view(self, request, object_id, extra_context=None):
        info = self.model._meta.app_label, self.model._meta.model_name
        org = Organization.objects.get(pk=object_id)
        org.parent = None
        org.save(update_fields=('parent',))
        return HttpResponseRedirect(
            reverse('admin:%s_%s_change' % info, kwargs={'object_id': object_id}),
        )

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                '<path:object_id>/unmerge/',
                self.admin_site.admin_view(self.merge_view),
                name='%s_%s_unmerge' % info
            ),
        ] + super().get_urls()

    def get_inline_instances(self, request, obj=None):
        if obj and obj.related_childs.exists():
            return super().get_inline_instances(request, obj=obj)
        return []

    def get_exclude(self, request, obj=None):
        if request.GET.get('show_parent', False):
            return
        return self.exclude

    def get_search_results(self, request, qs, term):
        qs, search_use_distinct = super().get_search_results(request, qs, term)
        # NOTE: Only show root organizations (Having no parents)
        qs = qs.filter(parent=None)
        return qs, search_use_distinct

    def log_merge(self, request, object, object_repr):
        """
        Log that an object will be merged. Note that this method must be
        called before the merging.
        """
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=admin.options.get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=object_repr,
            action_flag=CHANGE,
            change_message=f'Merged organization',
        )

    def get_merged_objects(self, objs, request):
        try:
            obj = objs[0]
        except IndexError:
            return [], [], False
        perms_needed = not self.has_merge_permission(request)
        to_merge = objs.all()
        count = ([obj._meta.verbose_name_plural, len(objs)],)
        return to_merge, count, perms_needed

    def merge_queryset(self, request, selected_parent_org_id, queryset):
        def update_children(related_childs):
            org_list = []
            for child_org in related_childs.all():
                if child_org.related_childs.exists():
                    org_list.extend(
                        update_children(
                            child_org.related_childs
                        )
                    )
                org_list.append(child_org)
            return org_list
        orgs = update_children(queryset)
        # Make others childern to selected_parent_organization
        Organization.objects.filter(
            id__in=[org.pk for org in orgs]
        ).update(parent=selected_parent_org_id)
        # Make selected_parent_organization a root entity
        Organization.objects.filter(pk=selected_parent_org_id).update(parent=None)
