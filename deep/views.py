from rest_framework.exceptions import NotFound
from rest_framework import status
from rest_framework.views import APIView

from django.views.generic import View
from django.conf import settings
from django.template.response import TemplateResponse


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


class Api_404View(APIView):
    def get(self, request, version):
        raise NotFound(detail="Error 404, page not found",
                       code=status.HTTP_404_NOT_FOUND)


class PasswordReset(View):
    """
    Template view for password reset email
    NOTE: Use Only For Debug
    """
    def get(self, request):
        from user.models import User
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        user = User.objects.get(pk=1)
        context = {
            'email': user.email,
            'domain': 'localhost:8000',
            'site_name': 'DEEPER',
            'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
            'user': user,
            'welcome': True,
            'token': default_token_generator.make_token(user),
            'protocol': 'https' if True else 'http',
        }
        return TemplateResponse(
            request, 'registration/password_reset_email.html', context)


class AccountActivate(View):
    """
    Template view for account activate email
    NOTE: Use Only For Debug
    """
    def get(self, request):
        from user.models import User
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        user = User.objects.get(pk=1)
        context = {
            'email': user.email,
            'domain': 'localhost:8000',
            'site_name': 'DEEPER',
            'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
            'user': user,
            'welcome': True,
            'token': default_token_generator.make_token(user),
            'protocol': 'https' if True else 'http',
        }
        return TemplateResponse(
            request, 'registration/user_activation_email.html', context)
