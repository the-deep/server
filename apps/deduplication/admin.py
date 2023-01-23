from django.contrib import admin

from .models import LSHIndex, DeduplicationRequest, LeadHash


@admin.register(LSHIndex)
class LSHIndexAdmin(admin.ModelAdmin):
    pass


@admin.register(DeduplicationRequest)
class DeduplicationRequestAdmin(admin.ModelAdmin):
    pass


@admin.register(LeadHash)
class LeadHashAdmin(admin.ModelAdmin):
    pass
