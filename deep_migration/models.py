from django.contrib.auth.models import User
from django.db import models
from geo.models import (
    Region,
    AdminLevel,
)
from user_group.models import UserGroup
from project.models import Project
from lead.models import Lead
from analysis_framework.models import AnalysisFramework


class BaseMigration(models.Model):
    first_migrated_at = models.DateTimeField(auto_now_add=True)
    last_migrated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-first_migrated_at']


class UserMigration(models.Model):
    old_id = models.IntegerField(unique=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        default=None, blank=True, null=True,
    )


class CountryMigration(BaseMigration):
    code = models.CharField(max_length=50, unique=True)
    region = models.ForeignKey(
        Region, on_delete=models.CASCADE,
        default=None, blank=True, null=True,
    )


class AdminLevelMigration(BaseMigration):
    old_id = models.IntegerField(unique=True)
    admin_level = models.ForeignKey(
        AdminLevel, on_delete=models.CASCADE,
        default=None, blank=True, null=True,
    )


class ProjectMigration(BaseMigration):
    old_id = models.IntegerField(unique=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        default=None, blank=True, null=True,
    )


class LeadMigration(BaseMigration):
    old_id = models.IntegerField(unique=True)
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE,
        default=None, blank=True, null=True,
    )


class AnalysisFrameworkMigration(BaseMigration):
    old_id = models.IntegerField(unique=True)
    analysis_framework = models.ForeignKey(
        AnalysisFramework, on_delete=models.CASCADE,
        default=None, blank=True, null=True,
    )


class UserGroupMigration(BaseMigration):
    old_id = models.IntegerField(unique=True)
    user_group = models.ForeignKey(
        UserGroup, on_delete=models.CASCADE,
        default=None, blank=True, null=True,
    )
