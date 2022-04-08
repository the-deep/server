import logging
import datetime

from celery import shared_task
from user_agents import parse

from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.template import loader
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives

from .token import unsubscribe_email_token_generator
from project.models import ProjectJoinRequest
from project.token import project_request_token_generator
from .models import Profile, EmailCondition


logger = logging.getLogger(__name__)


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


def send_mail_to_user(user, email_type, context={}, *args, **kwargs):
    """
    Validates email request
    Add common context variable
    """
    if user.profile.invalid_email:
        logger.warning(
            '[{}] Email not sent: User <{}>({}) email flagged as invalid email!!'.format(
                email_type, user.email, user.pk,
            )
        )
        return
    elif not user.profile.is_email_subscribed_for(email_type):
        logger.warning(
            '[{}] Email not sent: User <{}>({}) has not subscribed!!'.format(
                email_type, user.email, user.pk,
            )
        )
        return

    context.update({
        'client_domain': settings.DEEPER_FRONTEND_HOST,
        'protocol': settings.HTTP_PROTOCOL,
        'site_name': settings.DEEPER_SITE_NAME,
        'domain': settings.DJANGO_API_HOST,
        'user': user,
        'email_type': email_type,
        'unsubscribe_email_types': Profile.EMAIL_CONDITIONS_TYPES,
        'unsubscribe_email_token':
            unsubscribe_email_token_generator.make_token(user),
        'unsubscribe_email_id':
            urlsafe_base64_encode(force_bytes(user.pk)),
    })

    _send_mail(
        *args, **kwargs,
        context=context,
        from_email=settings.EMAIL_FROM,
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
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
        'welcome': welcome,
    }
    send_mail_to_user(
        user, EmailCondition.PASSWORD_RESET,
        context=context,
        subject_template_name='registration/password_reset_subject.txt',
        email_template_name='registration/password_reset_email.html',
    )


def send_account_activation(user):
    """
    Generate a one-use only link for account activation and send it to the
    user.
    """
    context = {
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    }
    send_mail_to_user(
        user, EmailCondition.ACCOUNT_ACTIVATION,
        context=context,
        subject_template_name='registration/user_activation_subject.txt',
        email_template_name='registration/user_activation_email.html',
    )


@shared_task
def send_project_join_request_emails(join_request_id):
    """
    Email Notification For Project Join
    """
    join_request = ProjectJoinRequest.objects.get(id=join_request_id)
    project = join_request.project
    request_by = join_request.requested_by
    reason = join_request.data['reason']
    request_data = {'join_request': join_request}
    email_type = EmailCondition.JOIN_REQUESTS

    context = {
        'request_by': request_by,
        'project': project,
        'reason': reason,
        'pid': urlsafe_base64_encode(force_bytes(join_request.pk)),
    }

    for user in project.get_admins():
        request_data.update({'will_responded_by': user})
        context.update({
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token':
                project_request_token_generator.make_token(request_data)
        })

        send_mail_to_user(
            user, email_type,
            context=context,
            subject_template_name='project/project_join_request.txt',
            email_template_name='project/project_join_request_email.html',
        )


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_type(request):
    http_agent = request.META.get('HTTP_USER_AGENT')
    if http_agent:
        user_agent = parse(http_agent)
        return user_agent.browser.family + ',' + user_agent.os.family
    return


@shared_task
def send_password_changed_notification(user_id, client_ip, device_type):
    user = User.objects.get(pk=user_id)
    context = {
        'time': datetime.datetime.now(),
        'location': client_ip,
        'device': device_type,
    }
    send_mail_to_user(
        user, email_type=EmailCondition.PASSWORD_CHANGED,
        context=context,
        subject_template_name='password_changed/subject.txt',
        email_template_name='password_changed/email.html',
    )


def generate_hidden_email(email):
    email_first_text = email.split('@')[0]
    email_last_text = email.split('@')[1]
    len_email_first_text = len(email_first_text)

    if len_email_first_text > 4:
        email_prefix = email_first_text[:2]
        email_suffix = email_first_text[-2:]

    if 1 <= len_email_first_text <= 4:
        email_prefix = email_first_text[:1]
        email_suffix = email_first_text[-1:]

    email_display = email_prefix + '***' + email_suffix + '@' + email_last_text
    return email_display
