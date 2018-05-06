from django.contrib import admin
from .models import String, Link


admin.site.register(String)
admin.site.register(Link)


# Uncomment for filtering strings in admin panel
# based on language
# @admin.register(String)
# class StringAdmin(admin.ModelAdmin):
#     pass
#
#
# @admin.register(Link)
# class LinkAdmin(admin.ModelAdmin):
#     def get_form(self, request, obj=None, **kwargs):
#         form = super(LinkAdmin, self).get_form(
#             request,
#             obj,
#             **kwargs,
#         )
#         if obj:
#             form.base_fields['string'].queryset = (
#                 form.base_fields['string'].queryset.filter(
#                     language=obj.language
#                 )
#             )
#
#         return form
