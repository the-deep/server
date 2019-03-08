from reversion.admin import VersionAdmin as _VersionAdmin
from django.contrib.postgres import fields
from django.contrib import admin

from jsoneditor.forms import JSONEditor


class JSONFieldMixin():
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditor},
    }


class ModelAdmin(JSONFieldMixin, admin.ModelAdmin):
    pass


class StackedInline(JSONFieldMixin, admin.StackedInline):
    pass


class VersionAdmin(JSONFieldMixin, _VersionAdmin):
    pass
