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
    LeadViewSet,
    LeadOptionsView,
    LeadExtractionTriggerView,
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
    Api_404View,
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

from django.conf.urls import (
    handler404
    # handler403, handler400, handler500
)

handler404 = Api_404View # noqa

router = routers.DefaultRouter()

# User routers
router.register(r'users', UserViewSet,
                base_name='user')

# File routers
router.register(r'files', FileViewSet,
                base_name='file')

# User group registers
router.register(r'user-groups', UserGroupViewSet,
                base_name='user_group')
router.register(r'group-memberships', GroupMembershipViewSet,
                base_name='group_membership')

# Project routers
router.register(r'projects', ProjectViewSet,
                base_name='project')
router.register(r'project-memberships', ProjectMembershipViewSet,
                base_name='project_membership')

# Geo routers
router.register(r'regions', RegionViewSet,
                base_name='region')
router.register(r'admin-levels', AdminLevelViewSet,
                base_name='admin_level')
router.register(r'admin-levels-upload', AdminLevelUploadViewSet,
                base_name='admin_level_upload')

# Lead routers
router.register(r'leads', LeadViewSet,
                base_name='lead')

# Entry routers
router.register(r'entries', EntryViewSet,
                base_name='entry_lead')
router.register(r'entry-attribute', AttributeViewSet,
                base_name='entry_attribute')
router.register(r'entry-filter-data', FilterDataViewSet,
                base_name='entry_filter_data')
router.register(r'entry-export-data', ExportDataViewSet,
                base_name='entry_export_data')

# Analysis routers
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

    # JWT Authentication
    url(get_api_path(r'token/$'),
        TokenObtainPairView.as_view()),

    url(get_api_path(r'token/hid/$'),
        HIDTokenObtainPairView.as_view()),

    url(get_api_path(r'token/refresh/$'),
        TokenRefreshView.as_view()),

    # Filter options
    url(get_api_path(r'lead-options/$'),
        LeadOptionsView.as_view()),

    # Lead extraction triggering api
    url(get_api_path(r'lead-extraction-trigger/(?P<lead_id>\d+)/$'),
        LeadExtractionTriggerView.as_view()),

    # Viewsets
    url(get_api_path(''), include(router.urls)),

    # Docs
    url(get_api_path(r'docs/'), DocsView.as_view()),

    # DRF auth, TODO: logout
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

] + static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    url(r'^$', FrontendView.as_view()),
    url(r'^api/', Api_404View.as_view()),
]
