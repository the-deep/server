from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CustomMaximumLengthValidator():
    def __init__(self, max_length=128):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                _("This password has exceed the limit of %(max_length)d characters"),
                code="password_too_long",
                params={'max_length': self.max_length},
            )

    def get_help_text(self):
        return _(
            "Your password must contain more than %(max_length)d characters."
            % {'max_length': self.max_length}
        )
