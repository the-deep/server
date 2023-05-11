from django.contrib import admin

from .models import AssessmentRegistry, MethodologyAttribute

# Register your models here.


@admin.register(AssessmentRegistry)
class AssessmentRegistryAdmin(admin.ModelAdmin):
    list_display = ('id',)


@admin.register(MethodologyAttribute)
class MethodlogyAttributeAdmin(admin.ModelAdmin):
    list_display = ('id',)
