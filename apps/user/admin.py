from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )
    search_fields = (
        'username', 'first_name', 'last_name', 'email', 'profile__language',
        'profile__organization',
    )
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff',
        'get_organization', 'get_language',
    )
    list_select_related = ('profile', )
    list_filter = UserAdmin.list_filter + (
        'profile__is_experimental', 'profile__is_early_access',
    )

    def get_organization(self, instance):
        return instance.profile.organization

    def get_language(self, instance):
        return instance.profile.language

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

    get_organization.short_description = 'Organization'
    get_language.short_description = 'Language'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)
