from celery import shared_task
from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.template import loader
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives

from project.models import Project


def _send_mail(subject_template_name, email_template_name,
               context, from_email, to_email,
               html_email_template_name=None):
    """
    Send a django.core.mail.EmailMultiAlternatives to `to_email`.
    """
    subject = loader.render_to_string(subject_template_name, context)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)
    email_message = EmailMultiAlternatives(
        subject, body, from_email, [to_email])
    email_message.attach_alternative(body, "text/html")
    if html_email_template_name is not None:
        html_email = loader.render_to_string(
            html_email_template_name, context)
        email_message.attach_alternative(html_email, 'text/html')
    email_message.send()


def send_mail_to_user(user, context={}, force_send=False, *args, **kwargs):
    """
    Validates email request
    Add common context variable
    """
    if True or force_send:  # TODO: use user.profile.receive_email For True
        context.update({
            'client_domain': settings.DEEPER_FRONTEND_HOST,
            'protocol': settings.HTTP_PROTOCOL,
            'site_name': settings.DEEPER_SITE_NAME,
            'domain': settings.DJANGO_API_HOST,
            'user': user,
        })

        return _send_mail(
            *args, **kwargs,
            context=context,
            from_email=None,
            to_email=user.email,
        )


def get_users(email):
    """Given an email, return matching user(s) who should receive a reset.
    This allows subclasses to more easily customize the default policies
    that prevent inactive users and users with unusable passwords from
    resetting their password.
    """
    active_users = User._default_manager.filter(**{
        '%s__iexact' % User.get_email_field_name(): email,
        'is_active': True,
    })
    return (u for u in active_users)


def send_password_reset(user, welcome=False):
    """
    Generate a one-use only link for resetting password and send it to the
    user.
    """
    context = {
        'email': user.email,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        'token': default_token_generator.make_token(user),
        'welcome': welcome,
    }
    send_mail_to_user(
        user=user,
        context=context,
        force_send=True,
        subject_template_name='registration/password_reset_subject.txt',
        email_template_name='registration/password_reset_email.html',
    )


def send_account_activation(user):
    """
    Generate a one-use only link for account activation and send it to the
    user.
    """
    context = {
        'email': user.email,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        'token': default_token_generator.make_token(user),
    }
    send_mail_to_user(
        user=user,
        context=context,
        force_send=True,
        subject_template_name='registration/user_activation_subject.txt',
        email_template_name='registration/user_activation_email.html',
    )


@shared_task
def send_project_join_request_emails(request_by_id, project_id):
    """
    Email Notification For Project Join
    """
    project = Project.objects.get(id=project_id)
    request_by = User.objects.get(id=request_by_id)

    context = {
        'request_by': request_by,
        'project': project,
    }

    for user in project.get_admins():
        send_mail_to_user(
            user=user,
            context=context,
            force_send=True,  # TODO: remove this
            subject_template_name='project/project_join_request.txt',
            email_template_name='project/project_join_request.html',
        )
