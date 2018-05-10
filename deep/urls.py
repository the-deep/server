"""deep URL Configuration
"""
from django.views.decorators.clickjacking import xframe_options_exempt
from deep.views import get_frontend_url
from django.views.generic.base import RedirectView
from django.conf.urls import url, include, static
from django.views.static import serve
from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.conf import settings
from rest_framework import routers

import autofixture

from user.views import (
    UserViewSet,
    PasswordResetView,
    user_activate_confirm,
)
from gallery.views import (
    FileViewSet,
    GoogleDriveFileViewSet,
    DropboxFileViewSet,
    FilePreviewViewSet,
    FileExtractionTriggerView,
)
from user_group.views import (
    GroupMembershipViewSet,
    UserGroupViewSet,
)
from project.views import (
    ProjectMembershipViewSet,
    ProjectOptionsView,
    ProjectViewSet,
)
from geo.views import (
    AdminLevelViewSet,
    RegionCloneView,
    RegionViewSet,
    GeoAreasLoadTriggerView,
    GeoJsonView,
    GeoBoundsView,
    GeoOptionsView,
)
from lead.views import (
    LeadGroupViewSet,
    LeadViewSet,
    LeadPreviewViewSet,
    LeadOptionsView,
    LeadExtractionTriggerView,
    LeadWebsiteFetch,

    WebInfoExtractView,
)
from entry.views import (
    EntryViewSet, AttributeViewSet, FilterDataViewSet,
    EntryFilterView,
    ExportDataViewSet,
    EntryOptionsView,
    EditEntriesDataViewSet,
)
from analysis_framework.views import (
    AnalysisFrameworkCloneView,
    AnalysisFrameworkViewSet,
    ExportableViewSet,
    FilterViewSet,
    WidgetViewSet,
)
from ary.views import (
    AssessmentViewSet,
    AssessmentOptionsView,
    AssessmentTemplateViewSet,
    LeadAssessmentViewSet,
)
from category_editor.views import (
    CategoryEditorViewSet,
    CategoryEditorCloneView,
    CategoryEditorClassifyView,
)
from connector.views import (
    SourceViewSet,
    ConnectorViewSet,
    ConnectorUserViewSet,
    ConnectorProjectViewSet,
)
from export.views import (
    ExportTriggerView,
    ExportViewSet,
)
from deep.views import (
    Api_404View,
    FrontendView,
    PasswordReset,
    AccountActivate,
)
from lang.views import (
    LanguageViewSet,
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

handler404 = Api_404View  # noqa

router = routers.DefaultRouter()

# User routers
router.register(r'users', UserViewSet,
                base_name='user')

# File routers
router.register(r'files', FileViewSet,
                base_name='file')
router.register(r'files-google-drive', GoogleDriveFileViewSet,
                base_name='file_google_drive')
router.register(r'files-dropbox', DropboxFileViewSet,
                base_name='file_dropbox')
router.register(r'file-previews', FilePreviewViewSet,
                base_name='file_preview')

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

# Lead routers
router.register(r'lead-groups', LeadGroupViewSet,
                base_name='lead_group')
router.register(r'leads', LeadViewSet,
                base_name='lead')
router.register(r'lead-previews', LeadPreviewViewSet,
                base_name='lead_preview')

# Entry routers
router.register(r'entries', EntryViewSet,
                base_name='entry_lead')
router.register(r'entry-attributes', AttributeViewSet,
                base_name='entry_attribute')
router.register(r'entry-filter-data', FilterDataViewSet,
                base_name='entry_filter_data')
router.register(r'entry-export-data', ExportDataViewSet,
                base_name='entry_export_data')
router.register(r'edit-entries-data', EditEntriesDataViewSet,
                base_name='edit_entries_data')

# Analysis framework routers
router.register(r'analysis-frameworks', AnalysisFrameworkViewSet,
                base_name='analysis_framework')
router.register(r'analysis-framework-widgets', WidgetViewSet,
                base_name='analysis_framework_widget')
router.register(r'analysis-framework-filters', FilterViewSet,
                base_name='analysis_framework_filter')
router.register(r'analysis-framework-exportables', ExportableViewSet,
                base_name='analysis_framework_exportable')

# Assessment registry
router.register(r'assessments', AssessmentViewSet,
                base_name='assessment')
router.register(r'lead-assessments', LeadAssessmentViewSet,
                base_name='lead_assessment')
router.register(r'assessment-templates', AssessmentTemplateViewSet,
                base_name='assessment_template')

# Category editor routers
router.register(r'category-editors', CategoryEditorViewSet,
                base_name='category_editor')

# Connector routers
router.register(r'connector-sources', SourceViewSet,
                base_name='connector_source')
router.register(r'connectors', ConnectorViewSet,
                base_name='connector')
router.register(r'connector-users', ConnectorUserViewSet,
                base_name='connector_users')
router.register(r'connector-projects', ConnectorProjectViewSet,
                base_name='connector_projects')

# Export routers
router.register(r'exports', ExportViewSet, base_name='export')

# Language routers
router.register(r'languages', LanguageViewSet, base_name='language')


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

    # Activate User
    url(r'^user/activate/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        user_activate_confirm,
        name='user_activate_confirm'),

    # password reset
    url(get_api_path(r'password/reset/$'),
        PasswordResetView.as_view()),

    url(r'^password/reset/done/$',
        auth_views.password_reset_done,
        name='password_rest_done'),

    url(r'^password/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        auth_views.password_reset_confirm,
        {
            'post_reset_redirect': '{}://{}/login/'.format(
                settings.HTTP_PROTOCOL, settings.DEEPER_FRONTEND_HOST)
        },
        name='password_reset_confirm'),

    url(r'^password/done/$',
        auth_views.password_reset_complete,
        name='password_reset_complete'),

    url(r'^password/change/$',
        auth_views.password_change,
        name='password_change'),

    url(r'^password/change/done/$',
        auth_views.password_change,
        name='password_change_done'),

    # Attribute options for various models
    url(get_api_path(r'lead-options/$'),
        LeadOptionsView.as_view()),
    url(get_api_path(r'assessment-options/$'),
        AssessmentOptionsView.as_view()),
    url(get_api_path(r'entry-options/$'),
        EntryOptionsView.as_view()),
    url(get_api_path(r'project-options/$'),
        ProjectOptionsView.as_view()),

    # Triggering api
    url(get_api_path(r'lead-extraction-trigger/(?P<lead_id>\d+)/$'),
        LeadExtractionTriggerView.as_view()),

    url(get_api_path(r'file-extraction-trigger/$'),
        FileExtractionTriggerView.as_view()),

    url(get_api_path(r'geo-areas-load-trigger/(?P<region_id>\d+)/$'),
        GeoAreasLoadTriggerView.as_view()),

    url(get_api_path(r'export-trigger/$'),
        ExportTriggerView.as_view()),

    # Website fetch api
    url(get_api_path(r'lead-website-fetch/$'),
        LeadWebsiteFetch.as_view()),

    url(get_api_path(r'web-info-extract/$'),
        WebInfoExtractView.as_view()),

    # Filter apis
    url(get_api_path(r'entries/filter/'), EntryFilterView.as_view()),

    url(get_api_path(
        r'projects/(?P<project_id>\d+)/category-editor/classify/'
    ), CategoryEditorClassifyView.as_view()),

    # Geojson api
    url(get_api_path(r'admin-levels/(?P<admin_level_id>\d+)/geojson/$'),
        GeoJsonView.as_view()),
    url(get_api_path(r'admin-levels/(?P<admin_level_id>\d+)/geojson/bounds/$'),
        GeoBoundsView.as_view()),
    url(get_api_path(r'geo-options/$'),
        GeoOptionsView.as_view()),

    # Clone apis
    url(get_api_path(r'clone-region/(?P<region_id>\d+)/$'),
        RegionCloneView.as_view()),
    url(get_api_path(r'clone-analysis-framework/(?P<af_id>\d+)/$'),
        AnalysisFrameworkCloneView.as_view()),
    url(get_api_path(r'clone-category-editor/(?P<ce_id>\d+)/$'),
        CategoryEditorCloneView.as_view()),

    # Viewsets
    url(get_api_path(''), include(router.urls)),

    # Docs
    url(get_api_path(r'docs/'), DocsView.as_view()),

    # DRF auth, TODO: logout
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

    # NOTE: For debuging email templates
    url(r'^pr-email/$', PasswordReset.as_view()),
    url(r'^aa-email/$', AccountActivate.as_view()),

    url(r'^favicon.ico$',
        RedirectView.as_view(
            url=get_frontend_url('favicon.ico'),
        ),
        name="favicon"),
] + static.static(
    settings.MEDIA_URL, view=xframe_options_exempt(serve),
    document_root=settings.MEDIA_ROOT)

urlpatterns += [
    url(r'^$', FrontendView.as_view()),
]

handler404 = Api_404View.as_view()
autofixture.autodiscover()
