from django.contrib import admin
from django.db.models import Count

from .models import UserGroup, GroupMembership


class UserGroupInline(admin.TabularInline):
    model = GroupMembership
    autocomplete_fields = ('member', 'added_by',)


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'member_count')
    inlines = [UserGroupInline]
    search_fields = ('title',)
    autocomplete_fields = ('display_picture',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            member_count=Count('members', distinct=True)
        )

    def member_count(self, instance):
        return instance.member_count
