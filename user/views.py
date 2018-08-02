from django.contrib.auth.models import User
from django.template.response import TemplateResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_text
from rest_framework import (
    exceptions,
    filters,
    permissions,
    response,
    status,
    views,
    viewsets,
)
from rest_framework.decorators import detail_route

from deep.views import get_frontend_url
from .token import unsubscribe_email_token_generator
from .serializers import (
    UserSerializer,
    UserPreferencesSerializer,
    NotificationSerializer,
    PasswordResetSerializer,
)


class UserPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user


class UserViewSet(viewsets.ModelViewSet):
    """
    create:
    Register a new user

    retrieve:
    Get an existing user

    list:
    Get a list of all users ordered by date joined

    destroy:
    Delete an existing user

    update:
    Modify an existing user

    partial_update:
    Modify an existing user partially
    """

    queryset = User.objects.filter(is_active=True).order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [UserPermission]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_object(self):
        pk = self.kwargs['pk']
        if pk == 'me':
            return self.request.user
        else:
            return super().get_object()

    @detail_route(
        permission_classes=[permissions.IsAuthenticated],
        url_path='preferences',
        serializer_class=UserPreferencesSerializer,
    )
    def get_preferences(self, request, pk=None, version=None):
        user = self.get_object()
        if user != request.user:
            raise exceptions.PermissionDenied()

        serializer = UserPreferencesSerializer(
            user,
            context={'request': request},
        )
        return response.Response(serializer.data)

    @detail_route(
        permission_classes=[permissions.IsAuthenticated],
        url_path='notifications',
        serializer_class=NotificationSerializer,
    )
    def get_notifications(self, request, pk=None, version=None):
        from user.notifications import generate_notifications
        user = self.get_object()
        if user != request.user:
            raise exceptions.PermissionDenied()

        notifications = generate_notifications(user)
        self.page = self.paginate_queryset(notifications)
        serializer = self.get_serializer(self.page, many=True)
        return self.get_paginated_response(serializer.data)


class PasswordResetView(views.APIView):
    def post(self, request, version=None):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(
            serializer.data, status=status.HTTP_201_CREATED)


def user_activate_confirm(
    request, uidb64, token,
    template_name='registration/user_activation_confirm.html',
    token_generator=default_token_generator,
):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    context = {
        'success': True,
        'login_url': get_frontend_url('login/'),
        'title': 'Account Activation',
    }

    if user is not None and token_generator.check_token(user, token):
        user.is_active = True
        user.profile.login_attempts = 0
        user.save()
    else:
        context['success'] = False

    return TemplateResponse(request, template_name, context)


def unsubscribe_email(
    request, uidb64, token, email_type,
    template_name='user/unsubscribe_email__confirm.html',
    token_generator=unsubscribe_email_token_generator,
):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    context = {
        'success': True,
        'title': 'Unsubscribe Email',
    }

    if user is not None and token_generator.check_token(user, token):
        # user.profile.receive_email = False
        user.profile.disable_email_receive(email_type)
        user.save()
    else:
        context['success'] = False

    return TemplateResponse(request, template_name, context)
