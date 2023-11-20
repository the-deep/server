# Register your models here.
from django.contrib import admin

from assisted_tagging.models import AssistedTaggingModelPredictionTag, AssistedTaggingPrediction, DraftEntry
from deep.admin import VersionAdmin


@admin.register(DraftEntry)
class DraftEntryAdmin(VersionAdmin):
    list_display = [
        'lead',
        'prediction_status',
        'excerpt',
    ]


@admin.register(AssistedTaggingPrediction)
class AssistedTaggingPredictionAdmin(VersionAdmin):
    list_display = [
        "data_type",
        "draft_entry",
        "value"
    ]


@admin.register(AssistedTaggingModelPredictionTag)
class AssistedTaggingModelPredictionTagAdmin(VersionAdmin):
    list_display = [
        'name',
        'is_category',
        'tag_id',
    ]
