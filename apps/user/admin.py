from django.contrib import admin
from django.db import models
from django.contrib.auth.admin import UserAdmin
from .models import (
    Profile, User, Feature, EmailDomain,
    gen_auth_proxy_model, OTP_MODELS, OTP_PROXY_MODELS
)


admin.site.unregister(User)
for _, model, _ in OTP_MODELS:
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


# Register OTP Proxy Model Dynamically
for model, model_admin in OTP_PROXY_MODELS:
    class DjangoOTPAdmin(model_admin):
        search_fields = [f'user__{user_prop}' for user_prop in CustomUserAdmin.search_fields]
        list_display = ('user', 'name', 'confirmed') if len(model_admin.list_display) <= 1 else model_admin.list_display
        autocomplete_fields = ('user',)
    admin.site.register(model, DjangoOTPAdmin)


@admin.register(gen_auth_proxy_model(Feature))
class CustomFeature(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('title', 'feature_type', 'user_count',)
    filter_horizontal = ('users', 'email_domains',)

    def get_readonly_fields(self, request, obj=None):
        # editing an existing object
        if obj:
            return self.readonly_fields + ('key', )
        return self.readonly_fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def user_count(self, instance):
        if not instance:
            return
        query = models.Q(pk__in=instance.users.values_list('pk', flat=True))
        for item in [
            models.Q(username__iendswith=domain_name)
            for domain_name in instance.email_domains.values_list('domain_name', flat=True)
        ]:
            query |= item
        return User.objects.filter(query).distinct().count()

    user_count.short_description = 'User Count'


@admin.register(gen_auth_proxy_model(EmailDomain))
class EmailDoaminAdmin(admin.ModelAdmin):
    search_fields = ('title', 'domain_name')
    list_display = ('title', 'domain_name', 'user_count')

    def user_count(self, instance):
        if instance:
            return User.objects.filter(
                username__iendswith=instance.domain_name,
            ).distinct().count()

    user_count.short_description = 'User Count'
