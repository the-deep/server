from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry,
    DiscardedEntry
)


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    pass


@admin.register(AnalysisPillar)
class AnalysisPillarAdmin(VersionAdmin):
    pass


class AnalyticalStatementEntryInline(admin.TabularInline):
    model = AnalyticalStatementEntry


@admin.register(AnalyticalStatement)
class AnalyticalStatementAdmin(admin.ModelAdmin):
    inlines = [AnalyticalStatementEntryInline]


@admin.register(DiscardedEntry)
class DiscardedEntryAdmin(admin.ModelAdmin):
    pass
