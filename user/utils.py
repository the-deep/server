from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.template import loader
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives


def send_mail(subject_template_name, email_template_name,
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


def send_password_reset(
    email, users=None, domain_override=None, welcome=False,
    subject_template_name='registration/password_reset_subject.txt',
    email_template_name='registration/password_reset_email.html',
    use_https=settings.HTTP_PROTOCOL == 'https',
    token_generator=default_token_generator, from_email=None, request=None,
    html_email_template_name=None, extra_email_context=None
):
    """
    Generate a one-use only link for resetting password and send it to the
    user.
    """
    for user in users or get_users(email):
        if not domain_override:
            site_name = settings.DEEPER_SITE_NAME
            domain = settings.DJANGO_API_HOST
        else:
            site_name = domain = domain_override
        context = {
            'email': email,
            'domain': domain,
            'site_name': site_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
            'user': user,
            'welcome': welcome,
            'token': token_generator.make_token(user),
            'protocol': 'https' if use_https else 'http',
            **(extra_email_context or {}),
        }
        send_mail(
            subject_template_name, email_template_name, context,
            from_email, email,
            html_email_template_name=html_email_template_name,
        )


def send_account_activation(
    user=None, domain_override=None,
    subject_template_name='registration/user_activation_subject.txt',
    email_template_name='registration/user_activation_email.html',
    use_https=settings.HTTP_PROTOCOL == 'https',
    token_generator=default_token_generator, from_email=None, request=None,
    html_email_template_name=None, extra_email_context=None
):
    """
    Generate a one-use only link for account activation and send it to the
    user.
    """
    if not domain_override:
        site_name = settings.DEEPER_SITE_NAME
        domain = settings.DJANGO_API_HOST
    else:
        site_name = domain = domain_override
    context = {
        'email': user.email,
        'domain': domain,
        'site_name': site_name,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        'user': user,
        'token': token_generator.make_token(user),
        'protocol': 'https' if use_https else 'http',
        **(extra_email_context or {}),
    }
    send_mail(
        subject_template_name, email_template_name, context,
        from_email, user.email,
        html_email_template_name=html_email_template_name,
    )
