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

# import autofixture

from user.views import (
    UserViewSet,
    PasswordResetView,
    user_activate_confirm,
    unsubscribe_email,
)
from gallery.views import (
    FileView,
    FileViewSet,
    GoogleDriveFileViewSet,
    DropboxFileViewSet,
    FilePreviewViewSet,
    FileExtractionTriggerView,
    MetaExtractionView,
    PublicFileView,
)
from tabular.views import (
    BookViewSet,
    SheetViewSet,
    FieldViewSet,
    GeodataViewSet,
    TabularExtractionTriggerView,
    TabularGeoProcessTriggerView,
)
from user_group.views import (
    GroupMembershipViewSet,
    UserGroupViewSet,
)
from project.views import (
    ProjectMembershipViewSet,
    ProjectUserGroupViewSet,
    ProjectOptionsView,
    ProjectRoleViewSet,
    ProjectViewSet,
    ProjectStatViewSet,
    accept_project_confirm,
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
    LeadGroupAssessmentViewSet,
)
from category_editor.views import (
    CategoryEditorViewSet,
    CategoryEditorCloneView,
    CategoryEditorClassifyView,
)
from connector.views import (
    SourceViewSet,
    SourceQueryView,
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
    CombinedView,
    FrontendView,
    PasswordReset,
    ProjectJoinRequest,
    AccountActivate,
)
from organization.views import (
    OrganizationViewSet,
)
from lang.views import (
    LanguageViewSet,
)
from docs.views import (
    DocsView,
)
from client_page_meta.views import (
    PageViewSet,
)

from notification.views import (
    NotificationViewSet,
)

from jwt_auth.views import (
    HIDTokenObtainPairView,
    TokenObtainPairView,
    TokenRefreshView,
)
from commons.views import (
    RenderChart,
)

from django.conf.urls import (
    handler404
    # handler403, handler400, handler500
)

handler404 = Api_404View  # noqa

router = routers.DefaultRouter()

# User routers
router.register(r'users', UserViewSet,
                basename='user')

# File routers
router.register(r'files', FileViewSet,
                basename='file')
router.register(r'files-google-drive', GoogleDriveFileViewSet,
                basename='file_google_drive')
router.register(r'files-dropbox', DropboxFileViewSet,
                basename='file_dropbox')
router.register(r'file-previews', FilePreviewViewSet,
                basename='file_preview')

# Tabular routers
router.register(r'tabular-books', BookViewSet,
                basename='tabular_book')
router.register(r'tabular-sheets', SheetViewSet,
                basename='tabular_sheet')
router.register(r'tabular-fields', FieldViewSet,
                basename='tabular_field')
router.register(r'tabular-geodatas', GeodataViewSet,
                basename='tabular_geodata')

# User group registers
router.register(r'user-groups', UserGroupViewSet,
                basename='user_group')
router.register(r'group-memberships', GroupMembershipViewSet,
                basename='group_membership')

# Project routers
router.register(r'projects', ProjectViewSet,
                basename='project')
router.register(r'projects-stat', ProjectStatViewSet,
                basename='project-stat')
router.register(r'project-roles', ProjectRoleViewSet,
                basename='project_role')
router.register(r'project-memberships', ProjectMembershipViewSet,
                basename='project_membership')
router.register(r'project-usergroups', ProjectUserGroupViewSet,
                basename='project_usergroup')

# Geo routers
router.register(r'regions', RegionViewSet,
                basename='region')
router.register(r'admin-levels', AdminLevelViewSet,
                basename='admin_level')

# Lead routers
router.register(r'lead-groups', LeadGroupViewSet,
                basename='lead_group')
router.register(r'leads', LeadViewSet,
                basename='lead')
router.register(r'lead-previews', LeadPreviewViewSet,
                basename='lead_preview')

# Entry routers
router.register(r'entries', EntryViewSet,
                basename='entry_lead')
router.register(r'entry-attributes', AttributeViewSet,
                basename='entry_attribute')
router.register(r'entry-filter-data', FilterDataViewSet,
                basename='entry_filter_data')
router.register(r'entry-export-data', ExportDataViewSet,
                basename='entry_export_data')
router.register(r'edit-entries-data', EditEntriesDataViewSet,
                basename='edit_entries_data')

# Analysis framework routers
router.register(r'analysis-frameworks', AnalysisFrameworkViewSet,
                basename='analysis_framework')
router.register(r'analysis-framework-widgets', WidgetViewSet,
                basename='analysis_framework_widget')
router.register(r'analysis-framework-filters', FilterViewSet,
                basename='analysis_framework_filter')
router.register(r'analysis-framework-exportables', ExportableViewSet,
                basename='analysis_framework_exportable')

# Assessment registry
router.register(r'assessments', AssessmentViewSet,
                basename='assessment')
router.register(r'lead-assessments', LeadAssessmentViewSet,
                basename='lead_assessment')
router.register(r'lead-group-assessments', LeadGroupAssessmentViewSet,
                basename='lead_group_assessment')
router.register(r'assessment-templates', AssessmentTemplateViewSet,
                basename='assessment_template')

# Category editor routers
router.register(r'category-editors', CategoryEditorViewSet,
                basename='category_editor')

# Connector routers
router.register(r'connector-sources', SourceViewSet,
                basename='connector_source')
router.register(r'connectors', ConnectorViewSet,
                basename='connector')
router.register(r'connector-users', ConnectorUserViewSet,
                basename='connector_users')
router.register(r'connector-projects', ConnectorProjectViewSet,
                basename='connector_projects')

# Organization routers
router.register(r'organizations', OrganizationViewSet, basename='organization')

# Export routers
router.register(r'exports', ExportViewSet, basename='export')

# Notification routers
router.register(r'notifications',
                NotificationViewSet, basename='notification')

# Language routers
router.register(r'languages', LanguageViewSet, basename='language')

# Page routers
router.register(r'pages', PageViewSet, basename='page')


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

    # Gallery
    url(r'^file/(?P<file_id>\d+)/$', FileView.as_view(), name='file'),
    url(
        r'^public-file/(?P<fidb64>[0-9A-Za-z]+)/(?P<token>.+)/(?P<filename>.*)$',
        PublicFileView.as_view(),
        name='gallery_public_url',
    ),

    # Activate User
    url(r'^user/activate/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        user_activate_confirm,
        name='user_activate_confirm'),

    # Unsubscribe User Email
    url(r'^user/unsubscribe/email/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/'
        '(?P<email_type>[A-Za-z_]+)/$',
        unsubscribe_email,
        name='unsubscribe_email'),
    # Project Request Accept
    url(r'^project/join-request/'
        '(?P<uidb64>[0-9A-Za-z]+)-(?P<pidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        accept_project_confirm,
        name='accept_project_confirm'),

    # password reset API
    url(get_api_path(r'password/reset/$'),
        PasswordResetView.as_view()),

    # Password Reset
    url(r'^password/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        auth_views.PasswordResetConfirmView.as_view(
            success_url='{}://{}/login/'.format(
                settings.HTTP_PROTOCOL, settings.DEEPER_FRONTEND_HOST,
            )
        ),
        name='password_reset_confirm'),

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

    url(get_api_path(r'meta-extraction/(?P<file_id>\d+)/$'),
        MetaExtractionView.as_view()),

    url(get_api_path(r'geo-areas-load-trigger/(?P<region_id>\d+)/$'),
        GeoAreasLoadTriggerView.as_view()),

    url(get_api_path(r'export-trigger/$'),
        ExportTriggerView.as_view()),

    url(get_api_path(r'tabular-extraction-trigger/(?P<book_id>\d+)/$'),
        TabularExtractionTriggerView.as_view()),

    url(get_api_path(r'tabular-geo-extraction-trigger/(?P<field_id>\d+)/$'),
        TabularGeoProcessTriggerView.as_view()),

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

    # Source query api
    url(get_api_path(
        r'connector-sources/(?P<source_type>[-\w]+)/(?P<query>[-\w]+)/',
    ), SourceQueryView.as_view()),

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

    # Combined API View
    url(get_api_path(r'combined/$'), CombinedView.as_view()),

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
    url(r'^pj-email/$', ProjectJoinRequest.as_view()),
    url(r'^render-debug/$', RenderChart.as_view()),

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

# TODO Uncomment after fixing custom autofixtures
# autofixture.autodiscover()
