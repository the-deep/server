"""deep URL Configuration
"""
from django.conf.urls import url, include, static
from django.contrib import admin
from django.conf import settings

from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view
# from rest_framework.documentation import include_docs_urls

from user.views import (
    UserViewSet,
)
from gallery.views import (
    FileViewSet,
)
from user_group.views import (
    UserGroupViewSet,
    GroupMembershipViewSet,
)
from project.views import (
    ProjectViewSet,
    ProjectMembershipViewSet,
)
from geo.views import (
    RegionViewSet,
    AdminLevelViewSet,
    AdminLevelUploadViewSet,
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
from deep.views import FrontendView

from jwt_auth.views import (
    TokenObtainPairView,
    TokenRefreshView,
    HIDTokenObtainPairView,
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


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^api/v1/token/$', TokenObtainPairView.as_view()),
    url(r'^api/v1/token/hid/$', HIDTokenObtainPairView.as_view()),
    url(r'^api/v1/token/refresh/$', TokenRefreshView.as_view()),

    url(r'^api/v1/', include(router.urls)),

    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

    # url(r'^docs/', include_docs_urls(title='DEEP API')),
    url(r'^api/v1/docs/', get_swagger_view(title='DEEP API')),
] + static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    url(r'^', FrontendView.as_view()),
]
