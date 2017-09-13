from django.contrib import admin
from .models import UserGroup, GroupMembership


class UserGroupInline(admin.TabularInline):
    model = GroupMembership


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    inlines = [UserGroupInline]
