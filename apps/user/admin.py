from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Profile, User, Feature, EmailDomain,
    OPT_MODELS, OPT_PROXY_MODELS
)


admin.site.unregister(User)
for _, model in OPT_MODELS:
    admin.site.unregister(model)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    search_fields = (
        'username', 'first_name', 'last_name', 'email', 'profile__language',
        'profile__organization',
    )
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff',
        'get_organization', 'get_language',
    )
    list_select_related = ('profile', )
    list_filter = UserAdmin.list_filter + ('profile__invalid_email', )

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


class DjangoOTPAdmin(admin.ModelAdmin):
    search_fields = [f'user__{user_prop}' for user_prop in CustomUserAdmin.search_fields]
    list_display = ('user', 'name', 'confirmed')


# Register OPT Proxy Model Dynamically
for model in OPT_PROXY_MODELS:
    admin.site.register(model, DjangoOTPAdmin)


@admin.register(Feature)
class CustomFeature(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        # editing an existing object
        if obj:
            return self.readonly_fields + ('key', )
        return self.readonly_fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(EmailDomain)
