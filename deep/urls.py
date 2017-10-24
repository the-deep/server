"""deep URL Configuration
"""
from django.conf.urls import url, include, static
from django.contrib import admin
from django.conf import settings

from rest_framework import routers

from user.views import (
    UserViewSet,
)
from gallery.views import (
    FileViewSet,
)
from user_group.views import (
    GroupMembershipViewSet,
    UserGroupViewSet,
)
from project.views import (
    ProjectMembershipViewSet,
    ProjectViewSet,
)
from geo.views import (
    AdminLevelUploadViewSet,
    AdminLevelViewSet,
    RegionViewSet,
)
from lead.views import (
    LeadViewSet
)
from entry.views import (
    EntryViewSet, AttributeViewSet, FilterDataViewSet,
    ExportDataViewSet
)
from analysis_framework.views import (
    AnalysisFrameworkViewSet, WidgetViewSet, FilterViewSet,
    ExportableViewSet
)
from deep.views import (
    FrontendView,
)
from docs.views import (
    DocsView,
)

from jwt_auth.views import (
    HIDTokenObtainPairView,
    TokenObtainPairView,
    TokenRefreshView,
)


router = routers.DefaultRouter()
router.register(r'users', UserViewSet,
                base_name='user')
router.register(r'files', FileViewSet,
                base_name='file')
router.register(r'user-groups', UserGroupViewSet,
                base_name='user_group')
router.register(r'group-memberships', GroupMembershipViewSet,
                base_name='group_membership')
router.register(r'projects', ProjectViewSet,
                base_name='project')
router.register(r'project-memberships', ProjectMembershipViewSet,
                base_name='project_membership')
router.register(r'regions', RegionViewSet,
                base_name='region')
router.register(r'admin-levels', AdminLevelViewSet,
                base_name='admin_level')
router.register(r'admin-levels-upload', AdminLevelUploadViewSet,
                base_name='admin_level_upload')
router.register(r'leads', LeadViewSet,
                base_name='lead')

# Entry Routers
router.register(r'entries', EntryViewSet,
                base_name='entry_lead')
router.register(r'entry-attribute', AttributeViewSet,
                base_name='entry_attribute')
router.register(r'entry-filter-data', FilterDataViewSet,
                base_name='entry_filter_data')
router.register(r'entry-export-data', ExportDataViewSet,
                base_name='entry_export_data')

# Analysis Routers
router.register(r'analysis-framework', AnalysisFrameworkViewSet,
                base_name='analysis_framework')
router.register(r'analysis-framework-widget', WidgetViewSet,
                base_name='analysis_framework_widget')
router.register(r'analysis-framework-filter', FilterViewSet,
                base_name='analysis_framework_filter')
router.register(r'analysis-framework-exportable', ExportableViewSet,
                base_name='analysis_framework_exportable')


# Versioning : (v1|v2|v3)

API_PREFIX = r'^api/(?P<version>(v1))/'


def get_api_path(path):
    return '{}{}'.format(API_PREFIX, path)


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(get_api_path(r'token/$'),
        TokenObtainPairView.as_view()),

    url(get_api_path(r'token/hid/$'),
        HIDTokenObtainPairView.as_view()),

    url(get_api_path(r'token/refresh/$'),
        TokenRefreshView.as_view()),

    url(get_api_path(''), include(router.urls)),
    url(get_api_path(r'docs/'), DocsView.as_view()),

    # url(get_api_path(''), include('drf_openapi.urls')),

    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

] + static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    url(r'^', FrontendView.as_view()),
]
