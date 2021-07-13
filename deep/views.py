from rest_framework.exceptions import NotFound
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
from graphene_django.views import (
    GraphQLView,
    HttpError,
    HttpResponseBadRequest,
    ExecutionResult,
    parse,
    get_operation_ast,
    HttpResponseNotAllowed,
    OperationType,
    validate,
)
from asgiref.sync import async_to_sync

from deep.graphene_context import GQLContext
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
            'email_type': 'entry_comment',

            'notification_type': Notification.ENTRY_COMMENT_ASSIGNEE_CHANGE,
            'Notification': Notification,
            'comment': comment,
        })
        return TemplateResponse(
            request, 'entry/comment_notification_email.html', context)


class CustomGraphQLView(GraphQLView):
    def get_context(self, request):
        return GQLContext(request)

    def execute_graphql_request(
        self, request, data, query, variables, operation_name, show_graphiql=False
    ):
        if not query:
            if show_graphiql:
                return None
            raise HttpError(HttpResponseBadRequest("Must provide query string."))

        try:
            document = parse(query)
        except Exception as e:
            return ExecutionResult(errors=[e])

        if request.method.lower() == "get":
            operation_ast = get_operation_ast(document, operation_name)
            if operation_ast and operation_ast.operation != OperationType.QUERY:
                if show_graphiql:
                    return None

                raise HttpError(
                    HttpResponseNotAllowed(
                        ["POST"],
                        "Can only perform a {} operation from a POST request.".format(
                            operation_ast.operation.value
                        ),
                    )
                )

        validation_errors = validate(self.schema.graphql_schema, document)
        if validation_errors:
            return ExecutionResult(data=None, errors=validation_errors)

        execute = async_to_sync(self.schema.execute_async)
        response = execute(
            source=query,
            root_value=self.get_root_value(request),
            variable_values=variables,
            operation_name=operation_name,
            context_value=self.get_context(request),
            middleware=self.get_middleware(request),
        )
        return response
