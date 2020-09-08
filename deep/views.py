from rest_framework.exceptions import NotFound
from rest_framework import (
    views,
    status,
    response,
)

from django.urls import resolve
from django.views.generic import View
from django.conf import settings
from django.template.response import TemplateResponse

from user.models import User, Profile
from project.models import Project
from entry.models import EntryComment
from notification.models import Notification


def get_frontend_url(path=''):
    return '{protocol}://{domain}/{path}'.format(
        protocol=settings.HTTP_PROTOCOL or 'http',
        domain=settings.DEEPER_FRONTEND_HOST or 'localhost:3000',
        path=path,
    )


class FrontendView(View):
    def get(self, request):
        # TODO: make nice redirect page
        context = {
            'frontend_url': get_frontend_url(),
        }
        return TemplateResponse(request, 'home/welcome.html', context)


class Api_404View(views.APIView):
    def get(self, request, exception):
        raise NotFound(detail="Error 404, page not found",
                       code=status.HTTP_404_NOT_FOUND)


class CombinedView(views.APIView):
    def get(self, request, version=None):
        apis = request.query_params.get('apis', None)
        if apis is None:
            return response.Response({})

        apis = apis.split(',')
        results = {}

        api_prefix = '/'.join(request.path_info.split('/')[:-2])
        for api in apis:
            url = '{}/{}/'.format(api_prefix, api.strip('/'))
            view, args, kwargs = resolve(url)
            kwargs['request'] = request._request
            api_response = view(*args, **kwargs)

            if api_response.status_code >= 400:
                return response.Response({
                    api: api_response.data
                }, status=api_response.status_code)
            results[api] = api_response.data

        return response.Response(results)


def get_basic_email_context():
    user = User.objects.get(pk=1)
    context = {
        'client_domain': settings.DEEPER_FRONTEND_HOST,
        'protocol': settings.HTTP_PROTOCOL,
        'site_name': settings.DEEPER_SITE_NAME,
        'domain': settings.DJANGO_API_HOST,
        'uid': 'fakeuid',
        'user': user,
        'unsubscribe_email_types': Profile.EMAIL_CONDITIONS_TYPES,
        'request_by': user,
        'token': 'faketoken',
        'unsubscribe_email_token': 'faketoken',
        'unsubscribe_email_id': 'fakeid',
    }
    return context


class ProjectJoinRequest(View):
    """
    Template view for project join request email
    NOTE: Use Only For Debug
    """
    def get(self, request):
        project = Project.objects.get(pk=1)
        context = get_basic_email_context()
        context.update({
            'email_type': 'join_requests',
            'project': project,
            'pid': 'fakeuid',
            'reason': 'I want to join this project \
                because this is closely related to my research. \
                Data from this project will help me alot.',
        })
        return TemplateResponse(
            request, 'project/project_join_request_email.html', context)


class PasswordReset(View):
    """
    Template view for password reset email
    NOTE: Use Only For Debug
    """
    def get(self, request):
        welcome = request.GET.get('welcome', 'false').upper() == 'TRUE'
        context = get_basic_email_context()
        context.update({'welcome': welcome})
        return TemplateResponse(
            request, 'registration/password_reset_email.html', context)


class AccountActivate(View):
    """
    Template view for account activate email
    NOTE: Use Only For Debug
    """
    def get(self, request):
        context = get_basic_email_context()
        return TemplateResponse(
            request, 'registration/user_activation_email.html', context)


class EntryCommentEmail(View):
    """
    Template view for entry commit email
    NOTE: Use Only For Debug
    """
    def get(self, request):
        comment_id = request.GET.get('comment_id')
        comment = (
            EntryComment.objects.get(pk=comment_id)
            if comment_id else EntryComment
            .objects
            .filter(parent=None)
            .first()
        )
        context = get_basic_email_context()
        context.update({
            'email_type': 'entry_comment',

            'notification_type': Notification.ENTRY_COMMENT_ASSIGNEE_CHANGE,
            'Notification': Notification,
            'comment': comment,
        })
        return TemplateResponse(
            request, 'entry/comment_notification_email.html', context)
