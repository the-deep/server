# Register your models here.
from admin_auto_filters.filters import AutocompleteFilterFactory
from assisted_tagging.models import (
    AssistedTaggingModelPredictionTag,
    AssistedTaggingPrediction,
    DraftEntry,
)
from django.contrib import admin

from deep.admin import VersionAdmin


@admin.register(DraftEntry)
class DraftEntryAdmin(VersionAdmin):
    search_fields = ["lead"]
    list_display = [
        "lead",
        "prediction_status",
    ]
    list_filter = (AutocompleteFilterFactory("Lead", "lead"), AutocompleteFilterFactory("Project", "project"), "type")

    autocomplete_fields = (
        "project",
        "lead",
        "related_geoareas",
    )


@admin.register(AssistedTaggingPrediction)
class AssistedTaggingPredictionAdmin(VersionAdmin):
    search_fields = ["draft_entry"]
    list_display = [
        "data_type",
        "draft_entry",
        "value",
        "is_selected",
        "tag",
    ]
    list_filter = (AutocompleteFilterFactory("DraftEntry", "draft_entry"),)
    # NOTE: Skipping model_version. Only few of them exists
    autocomplete_fields = ("draft_entry", "category", "tag")


@admin.register(AssistedTaggingModelPredictionTag)
class AssistedTaggingModelPredictionTagAdmin(VersionAdmin):
    search_fields = ["parent_tag"]
    list_display = [
        "name",
        "is_category",
        "tag_id",
        "parent_tag",
    ]
    autocomplete_fields = ("parent_tag",)
