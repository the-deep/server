from django.contrib import admin
from .models import (
    Notification,
    Assignment
)


@admin.register(Notification)
class Notification(admin.ModelAdmin):
    pass


@admin.register(Assignment)
class Assignment(admin.ModelAdmin):
    pass
