"""deep URL Configuration
"""
from django.conf.urls import url, include, static
from django.contrib import admin
from django.conf import settings

from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view
# from rest_framework.documentation import include_docs_urls
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from user.views import UserViewSet
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
from deep.views import FrontendView


router = routers.DefaultRouter()
router.register(r'users', UserViewSet,
                base_name='user')
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


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # Future reference: (v1|v2|v3...)

    url(r'^api/v1/token/$', TokenObtainPairView.as_view()),
    url(r'^api/v1/token/refresh/$', TokenRefreshView.as_view()),

    url(r'^api/v1/', include(router.urls)),

    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

    # url(r'^docs/', include_docs_urls(title='DEEP API')),
    url(r'^api/v1/docs/', get_swagger_view(title='DEEP API')),

    url(r'^', FrontendView.as_view()),
] + static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
