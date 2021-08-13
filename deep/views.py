from rest_framework.exceptions import NotFound, PermissionDenied
from django.core.exceptions import PermissionDenied as DjPermissionDenied
from rest_framework import (
    views,
    status,
    response,
)

from django.http import JsonResponse
from django.urls import resolve
from django.views.generic import View
from django.conf import settings
from django.template.response import TemplateResponse
from graphene_django.views import GraphQLView
from graphene_file_upload.django import FileUploadGraphQLView

from deep.graphene_context import GQLContext
from deep.exceptions import PermissionDeniedException
from user.models import User, Profile
from project.models import Project
from entry.models import EntryComment
from quality_assurance.models import EntryReviewComment, CommentType
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


class ProjectPublicVizView(View):
    """
    View for public viz view without user authentication
    """
    def get(self, request, project_stat_id, token):
        from project.views import _get_viz_data

        json_only = request.GET.get('format', 'html').upper() == 'json'
        project = Project.objects.get(entry_stats__id=project_stat_id)
        context, status_code = _get_viz_data(request, project, False, token)
        context['project_title'] = project.title
        if json_only:
            return JsonResponse(context, status=status_code)
        context['poll_url'] = f'{request.path}?format=json'
        return TemplateResponse(request, 'project/project_viz.html', context, status=status_code)


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
            'email_type': Profile.E_EMAIL_COMMENT,
            'notification_type': Notification.ENTRY_COMMENT_ASSIGNEE_CHANGE,
            'Notification': Notification,
            'comment': comment,
        })
        return TemplateResponse(
            request, 'entry/comment_notification_email.html', context)


class EntryReviewCommentEmail(View):
    """
    Template view for entry review commit email
    NOTE: Use Only For Debug
    """
    def get(self, request):
        comment_id = request.GET.get('comment_id')
        notification_type = request.GET.get('notification_type', Notification.ENTRY_REVIEW_COMMENT_ADD)
        comment = (
            EntryReviewComment.objects.get(pk=comment_id)
            if comment_id else EntryReviewComment.objects.first()
        )
        context = get_basic_email_context()
        context.update({
            'email_type': Profile.E_EMAIL_COMMENT,
            'notification_type': notification_type,
            'CommentType': CommentType,
            'Notification': Notification,
            'comment': comment,
        })
        return TemplateResponse(
            request, 'entry/review_comment_notification_email.html', context)


class CustomGraphQLView(FileUploadGraphQLView):
    def get_context(self, request):
        return GQLContext(request)

    @staticmethod
    def format_error(error):
        formatted_error = GraphQLView.format_error(error)
        original_error = getattr(error, 'original_error', None)
        extensions = {}
        if original_error:
            if hasattr(original_error, 'code'):
                extensions['code'] = str(error.original_error.code)
            elif type(original_error) in [PermissionDenied, DjPermissionDenied]:
                extensions['code'] = str(PermissionDeniedException.code)
                formatted_error['message'] = str(PermissionDeniedException.default_message)
            else:
                extensions['errorCode'] = str(status.HTTP_500_INTERNAL_SERVER_ERROR)
        formatted_error['extensions'] = extensions
        return formatted_error
