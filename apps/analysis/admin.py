from django.contrib import admin

from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry,
)


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    pass


@admin.register(AnalysisPillar)
class AnalysisPillarAdmin(admin.ModelAdmin):
    pass


class AnalyticalStatementEntryInline(admin.TabularInline):
    model = AnalyticalStatementEntry


@admin.register(AnalyticalStatement)
class AnalyticalStatementAdmin(admin.ModelAdmin):
    inlines = [AnalyticalStatementEntryInline]
