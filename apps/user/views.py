from django.contrib.auth.models import User
from django.db import models
from django.template.response import TemplateResponse
from django.contrib.auth import update_session_auth_hash
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
from rest_framework.decorators import action

from utils.db.functions import StrPos
from deep.views import get_frontend_url

from .token import unsubscribe_email_token_generator
from .serializers import (
    UserSerializer,
    UserPreferencesSerializer,
    NotificationSerializer,
    PasswordResetSerializer,
    PasswordChangeSerializer
)
from .permissions import UserPermission


class UserViewSet(viewsets.ReadOnlyModelViewSet):
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
    permission_classes = [permissions.IsAuthenticated, UserPermission]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)

    def get_object(self):
        pk = self.kwargs['pk']
        if pk == 'me':
            return self.request.user
        else:
            return super().get_object()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        # Check if project/framework exclusion query is present
        exclude_project = self.request.query_params.get(
            'members_exclude_project')
        exclude_framework = self.request.query_params.get(
            'members_exclude_framework')

        if exclude_project:
            queryset = queryset.filter(
                ~models.Q(projectmembership__project=exclude_project)
            ).distinct()

        if exclude_framework:
            queryset = queryset.filter(
                ~models.Q(framework_membership__framework_id=exclude_framework)
            )

        search_str = self.request.query_params.get('search')
        if search_str is None or not search_str.strip():
            return queryset

        return queryset.annotate(
            strpos=StrPos(
                models.functions.Lower(
                    models.functions.Concat(
                        'first_name', models.Value(' '), 'last_name',
                        models.Value(' '), 'email',
                        output_field=models.CharField()
                    )
                ),
                models.Value(search_str.lower(), models.CharField())
            )
        ).filter(strpos__gte=1).order_by('strpos')

    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        url_path='preferences',
        serializer_class=UserPreferencesSerializer,
    )
    def get_preferences(self, request, pk=None, version=None):
        user = self.get_object()
        if user != request.user:
            raise exceptions.PermissionDenied()

        serializer = self.get_serializer(user)
        return response.Response(serializer.data)

    @action(
        detail=True,
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

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        url_name="change_password",
        url_path='me/change-password',
        serializer_class=PasswordChangeSerializer,
        methods=['POST']
    )
    def change_password(self, request, pk=None, version=None):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={
                'request': request
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        update_session_auth_hash(request, request.user)
        return response.Response(status=status.HTTP_200_OK)


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
    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
    ):
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
<<<<<<< HEAD
    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
    ):
=======
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
>>>>>>> Add count for ignored and added sourcelead
        user = None

    context = {
        'success': True,
        'title': 'Unsubscribe Email',
    }

    if user is not None and token_generator.check_token(user, token):
        user.profile.unsubscribe_email(email_type)
        user.save()
    else:
        context['success'] = False

    return TemplateResponse(request, template_name, context)
