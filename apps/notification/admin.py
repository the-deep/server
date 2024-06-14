from django.contrib import admin

from .models import Assignment, Notification


@admin.register(Notification)
class Notification(admin.ModelAdmin):
    list_display = ("receiver", "project", "notification_type", "timestamp", "status")
    list_filter = ("notification_type", "status")


@admin.register(Assignment)
class Assignment(admin.ModelAdmin):
    pass
